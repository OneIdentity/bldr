import os
import pytest
import subprocess
from pathlib import Path
from typing import Mapping

from ..testutil import copytree


@pytest.fixture()
def git_env():
    env = os.environ.copy()
    env["GIT_COMMITTER_NAME"] = "Test Developer"
    env["GIT_COMMITTER_EMAIL"] = "test.developer@example.com"
    env["GIT_AUTHOR_NAME"] = env["GIT_COMMITTER_NAME"]
    env["GIT_AUTHOR_EMAIL"] = env["GIT_COMMITTER_NAME"]

    yield env


@pytest.fixture
def git_import(request,
               tmp_path: Path, asset_dir: Path, git_env: Mapping[str, str]) -> Path:
    project = request.param
    import_from = asset_dir.joinpath(project)
    repo_dir = tmp_path.joinpath(project)
    repo_dir.mkdir()
    subprocess.check_call(['git', 'init'], cwd=repo_dir)
    subprocess.check_call(['git', 'checkout', '-b', 'upstream'], cwd=repo_dir)

    copytree(import_from.joinpath('upstream'), repo_dir)
    subprocess.check_call(['git', 'add', '--all'], cwd=repo_dir)
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', 'Imported upstream'], cwd=repo_dir, env=git_env)

    subprocess.check_call(['git', 'checkout', '-b', 'ubuntu'], cwd=repo_dir)
    copytree(import_from.joinpath('debian'), repo_dir)
    subprocess.check_call(['git', 'add', '--all'], cwd=repo_dir)
    subprocess.check_call(['git', 'commit', '--no-verify', '--message', 'Imported debian'], cwd=repo_dir, env=git_env)

    subprocess.check_call(['git', 'checkout', '-b', 'master'], cwd=repo_dir)

    return repo_dir
