"""
    :copyleft: 2020 by IterFilesystem team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


from pathlib import Path

from poetry_publish.tests import test_project_setup

# IterFilesystem
import iterfilesystem

PACKAGE_ROOT = Path(iterfilesystem.__file__).parent.parent


def test_version():
    test_project_setup.test_version(
        package_root=PACKAGE_ROOT,
        version=iterfilesystem.__version__
    )


def test_poetry_check():
    test_project_setup.test_poetry_check(package_root=PACKAGE_ROOT)
