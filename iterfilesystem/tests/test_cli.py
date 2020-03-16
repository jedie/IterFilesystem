import logging
import sys

import pytest

# IterFilesystem
from iterfilesystem.bin.print_fs_stats import main
from iterfilesystem.tests import BaseTestCase
from iterfilesystem.tests.test_utils import verbose_get_capsys


class TestCli(BaseTestCase):
    def test_cli_help(self, caplog, capsys):

        with pytest.raises(SystemExit) as pytest_wrapped_e:
            main('--help')

        captured_out, captured_err = verbose_get_capsys(capsys)
        assert 'usage: print_fs_stats.py' in captured_out
        assert captured_err == ''

        assert pytest_wrapped_e.value.code == 0

        logs = caplog.text
        print('-' * 100)
        print(logs)
        print('-' * 100)

        assert logs == ''

    def test_cli_not_existing_directory(self, caplog, capsys):
        with caplog.at_level(logging.DEBUG, logger="iterfilesystem"):
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                main(
                    '--path', '/foo/bar/does/not/exists',
                )

        logs = caplog.text
        print('-' * 100)
        print(logs)
        print('-' * 100)

        assert "INFO Read/process: '/foo/bar/does/not/exists'..." in logs

        captured_out, captured_err = verbose_get_capsys(capsys)
        assert captured_err == ''

        if sys.platform == 'win32':
            assert (
                "ERROR: Directory does not exists: C:\\foo\\bar\\does\\not\\exists"
            ) in captured_out
        else:
            assert "ERROR: Directory does not exists: /foo/bar/does/not/exists" in captured_out

        assert pytest_wrapped_e.value.code == 1

    def test_cli_scan(self, capsys):
        main(
            '--path', str(self.package_path),
            '--skip_dir_patterns', *self.skip_dir_patterns,
            '--skip_file_patterns', *self.skip_file_patterns,
            '--debug'
        )

        captured_out, captured_err = verbose_get_capsys(capsys)

        assert 'usage: print_fs_stats.py' not in captured_out
        assert "'hash': " in captured_out
