import subprocess
import shutil
from pathlib import Path
from typing import Mapping

import pytest

from bldr.bldr import BLDR
from ..testutil import copytree, extract_deb


@pytest.fixture
def quilt_project_path(git_project_name: str, git_import: Path,
                       asset_dir: Path, git_env: Mapping[str, str]) -> Path:
    import_from = asset_dir.joinpath(git_project_name)

    subprocess.check_call(['git', 'tag', 'upstream-older', 'upstream'], cwd=git_import)
    subprocess.check_call(['git', 'tag', 'debian-older', 'ubuntu'], cwd=git_import)

    subprocess.check_call(['git', 'checkout', 'upstream'], cwd=git_import)
    copytree(import_from.joinpath('upstream-newer'), git_import, exist_ok=True)
    subprocess.check_call(['git', 'add', '--all'], cwd=git_import)
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', 'Imported newer upstream'], cwd=git_import, env=git_env)
    subprocess.check_call(['git', 'tag', 'upstream-newer'], cwd=git_import)

    subprocess.check_call(['git', 'checkout', 'ubuntu'], cwd=git_import)
    subprocess.check_call(['git', 'merge', 'upstream-newer', '--no-commit'], cwd=git_import, env=git_env)
    copytree(import_from.joinpath('debian-newer'), git_import, exist_ok=True)
    subprocess.check_call(['git', 'add', '--all'], cwd=git_import)
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', 'Imported debian newer version'], cwd=git_import, env=git_env)
    subprocess.check_call(['git', 'tag', 'debian-newer'], cwd=git_import)

    subprocess.check_call(['git', 'checkout', 'master'], cwd=git_import)
    subprocess.check_call(['git', 'reset', '--hard', 'ubuntu'], cwd=git_import)
    copytree(import_from.joinpath('master'), git_import, exist_ok=True)
    subprocess.check_call(['git', 'add', '--all'], cwd=git_import)
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', 'Our patches'], cwd=git_import, env=git_env)

    return git_import


def do_build(local_repo_dir: Path, quilt_project_path: Path, docker_from: str, tmp_path: Path, expected_output: str) -> None:
    bldr = BLDR(
        local_repo_dir=local_repo_dir,
        source_dir=quilt_project_path.parent,
        docker_from=docker_from,
    )
    bldr.build(quilt_project_path)

    quilt_proj_deb_file = list(local_repo_dir.glob('**/quilt-proj*.deb'))[0]

    extract_dir = tmp_path.joinpath('extracted')
    extract_dir.mkdir()
    extract_deb(quilt_proj_deb_file, extract_dir)

    output = subprocess.check_output(['usr/bin/am-i-quilted'], cwd=extract_dir).decode('utf-8')
    assert output == expected_output, "The script output should be what expected"

    shutil.rmtree(str(extract_dir), ignore_errors=True)


@pytest.mark.parametrize('git_project_name', ['test-quilt-proj'], indirect=True)
def test_quilt_project_build(git_project_name: str, local_repo_dir: Path, quilt_project_path: Path, docker_from: str, tmp_path: Path):
    subprocess.check_call(['git', 'checkout', 'debian-older'], cwd=quilt_project_path)
    expected_output = (
        "So I am a little script from upstream\n"
        "A little bit buggy though.\n"
        "But do you still love me?\n"
    )
    debian_older_local_repo_dir = local_repo_dir.joinpath('debian-older')
    do_build(debian_older_local_repo_dir, quilt_project_path, docker_from, tmp_path, expected_output)

    subprocess.check_call(['git', 'checkout', 'debian-newer'], cwd=quilt_project_path)
    expected_output = (
        "So I am a newer little script from upstream\n"
        "A little bit buggy though.\n"
        "But do you still love me?\n"
    )
    debian_newer_local_repo_dir = local_repo_dir.joinpath('debian-newer')
    do_build(debian_newer_local_repo_dir, quilt_project_path, docker_from, tmp_path, expected_output)

    subprocess.check_call(['git', 'checkout', 'master'], cwd=quilt_project_path)
    expected_output = (
        "So I am a newer little script from upstream\n"
        "A little bit buggy though.\n"
        "But do you still really love me?\n"
    )
    master_local_repo_dir = local_repo_dir.joinpath('master')
    do_build(master_local_repo_dir, quilt_project_path, docker_from, tmp_path, expected_output)

    debian_newer_dsc = debian_newer_local_repo_dir.joinpath(git_project_name, 'debs', 'quilt-proj_1.1-1ubuntu1.dsc')
    master_dsc = master_local_repo_dir.joinpath(git_project_name, 'debs', 'quilt-proj_1.1-1ubuntu1bb50.1.dsc')

    assert 'quilt-proj_1.1.orig.tar.gz' in debian_newer_dsc.read_text(), "The script should generate the same orig.tar.gz every time."
    assert 'quilt-proj_1.1.orig.tar.gz' in master_dsc.read_text(), "The script should generate the same orig.tar.gz every time."
