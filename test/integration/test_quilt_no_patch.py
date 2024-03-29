import subprocess
from pathlib import Path
from typing import Mapping

import pytest

from bldr.bldr import BLDR
from ..testutil import copytree, extract_deb

PACKAGE_NAME = 'quilt-no-patch'


def git_import_package(git_dir: Path, git_env: Mapping[str, str], branches_dir: Path):
    subprocess.check_call(['git', 'checkout', '-b', 'upstream'], cwd=git_dir)

    copytree(branches_dir.joinpath('upstream'), git_dir)
    subprocess.check_call(['git', 'add', '--all'], cwd=git_dir)
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', 'Imported upstream'], cwd=git_dir, env=git_env)

    subprocess.check_call(['git', 'checkout', '-b', 'ubuntu'], cwd=git_dir)
    copytree(branches_dir.joinpath('debian'), git_dir)
    subprocess.check_call(['git', 'add', '--all'], cwd=git_dir)
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', 'Imported debian'], cwd=git_dir, env=git_env)

    subprocess.check_call(['git', 'checkout', '-b', 'master'], cwd=git_dir)
    copytree(branches_dir.joinpath('master'), git_dir, exist_ok=True)
    subprocess.check_call(['git', 'add', '--all'], cwd=git_dir)
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', 'Our changes'], cwd=git_dir, env=git_env)


@pytest.fixture
def quilt_project_path(tmp_path: Path, asset_dir: Path, git_env: Mapping[str, str]) -> Path:
    quilt_project_dir = tmp_path.joinpath('quilt_project')
    quilt_project_dir.mkdir()
    subprocess.check_call(['git', 'init'], cwd=quilt_project_dir)
    git_import_package(quilt_project_dir, git_env, asset_dir.joinpath(PACKAGE_NAME))
    return quilt_project_dir


def test_quilt_project_build(local_repo_dir: Path, quilt_project_path: Path, docker_from: str, tmp_path: Path):
    bldr = BLDR(
        local_repo_dir=local_repo_dir,
        source_dir=quilt_project_path.parent,
        docker_from=docker_from,
    )
    bldr.build(quilt_project_path)

    quilt_proj_deb_file = list(local_repo_dir.glob('**/' + PACKAGE_NAME + '*.deb'))[0]

    extract_dir = tmp_path.joinpath('extracted')
    extract_dir.mkdir()
    extract_deb(quilt_proj_deb_file, extract_dir)

    content = extract_dir.joinpath('usr', 'share', 'doc', PACKAGE_NAME, 'README').read_text()
    assert content == "Hello patched world!\n", "The patched file should be correct."
