from pathlib import Path

from iterfilesystem.tests import BaseTestCase


class Test(BaseTestCase):
    def test_package_path(self):
        assert self.package_path.is_dir()

        assert Path(self.package_path, 'iterfilesystem').is_dir()

        own_path = Path(__file__)
        rel_path = own_path.relative_to(self.package_path)
        assert rel_path == Path("iterfilesystem/tests/test_base_test_case.py")
