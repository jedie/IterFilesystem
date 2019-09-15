import pytest
from iterfilesystem.bin.print_fs_stats import main
from iterfilesystem.tests import BaseTestCase


class TestCli(BaseTestCase):
    def test_cli_help(self, capsys):

        with pytest.raises(SystemExit) as pytest_wrapped_e:
            main('--help')

        captured = capsys.readouterr()
        assert 'usage: print_fs_stats.py' in captured.out
        assert captured.err == ''

        assert pytest_wrapped_e.value.code == 0

    def test_cli_scan(self, capsys):
        main(
            '--force_restart',
            '--complete_cleanup',
            '--skip_dirs', *self.skip_dirs,
            '--skip_filenames', *self.skip_filenames,
            '--path', str(self.package_path)
        )

        captured = capsys.readouterr()

        print(captured.out)
        assert 'usage: print_fs_stats.py' not in captured.out
        assert 'Force restart, by delete old persist queue data.' in captured.out
        assert 'total filesystem items' in captured.out
        assert 'Directory count' in captured.out
        assert 'Remove persist data' in captured.out

        print(captured.err)
        assert '00 worker thread empty: 100%' in captured.err
        assert '01 worker thread empty: 100%' in captured.err
        assert '02 worker thread empty: 100%' in captured.err
        assert '*** all items processed ***: 100%' in captured.err
