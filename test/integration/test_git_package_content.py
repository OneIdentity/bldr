from pathlib import Path
from typing import List, Tuple

import pytest

from bldr.bldr import BLDR
from ..testutil import extract_deb


@pytest.mark.parametrize(
    'git_project_name, git_project_master_changes, content_checks',
    [pytest.param('test-quilt-proj-onedir', False,
                  [('usr/share/doc/feeling/alone', "Hello, friend!\n"),
                   ('usr/share/doc/feeling/lonely', "I am a test.\n")],
                  id='onedir'),
     pytest.param('quilt-no-patch', True,
                  [('usr/share/doc/quilt-no-patch/README', "Hello patched world!\n")],
                  id='no_patch'),
    ],
    indirect=['git_project_name', 'git_project_master_changes'])
def test_git_package_content(local_repo_dir: Path, git_import: Path, docker_from: str,
                             tmp_path: Path, content_checks: List[Tuple[Path, str]]):
    bldr = BLDR(
        local_repo_dir=local_repo_dir,
        source_dir=git_import.parent,
        docker_from=docker_from,
    )
    bldr.build(git_import)

    deb_file = list(local_repo_dir.glob('**/*.deb'))[0]

    extract_dir = tmp_path.joinpath('extracted')
    extract_dir.mkdir()
    extract_deb(deb_file, extract_dir)

    for path, expected in content_checks:
        assert extract_dir.joinpath(path).read_text() == expected, "File content should be correct."
