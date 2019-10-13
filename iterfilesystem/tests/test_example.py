import hashlib
import logging
import os
import sys
from pathlib import Path

import pytest

# IterFilesystem
from iterfilesystem.example import calc_sha512
from iterfilesystem.tests import BaseTestCase
from iterfilesystem.tests.test_utils import (
    stats_helper2assertments,
    verbose_get_capsys
)

ON_TRAVIS = 'TRAVIS' in os.environ


class TestExample(BaseTestCase):
    def test_package_path(self, caplog, capsys):
        with caplog.at_level(logging.DEBUG):
            stats_helper = calc_sha512(
                top_path=self.package_path,
                skip_dir_patterns=self.skip_dir_patterns,
                skip_file_patterns=self.skip_file_patterns,
                wait=True
            )

        captured_out, captured_err = verbose_get_capsys(capsys)

        log_messages = '\n'.join([rec.message for rec in caplog.records])
        print('_' * 100)
        print('Captured logs:')
        print(log_messages)
        print('-' * 100)

        stats_helper.print_stats()

        assert stats_helper.collect_dir_item_count >= 40
        assert stats_helper.get_walker_dir_item_count() >= 40
        assert stats_helper.collect_file_size > 55000
        assert stats_helper.process_file_size > 55000

        assert 'SHA515 hash calculated over all file content:' in captured_out
        assert 'Total file size:' in captured_out

    def test_not_existing_path(self):
        with pytest.raises(NotADirectoryError):
            calc_sha512(
                top_path='/foo/bar/not/exists/',
            )

    def test_hash(self, tmp_path):
        hash = hashlib.sha512()
        for no in range(10):
            with Path(tmp_path, f'working_file_{no}.dat').open("wb") as f:
                data = b'X%i' % no
                f.write(data)
                hash.update(data)

        expected_hash = hash.hexdigest()

        stats_helper = calc_sha512(
            top_path=tmp_path
        )

        stats_helper2assertments(stats_helper)

        if not ON_TRAVIS:
            # FIXME: hash on appveyor.com and local are correct, but not on TravisCI, why?
            assert stats_helper.hash == expected_hash

        assert stats_helper.collect_dir_item_count == 10
        assert stats_helper.collect_file_size == 20

        assert stats_helper.process_error_count == 0
        assert stats_helper.process_file_size == 20
        assert stats_helper.process_files == 10

        assert stats_helper.walker_dir_count == 0
        assert stats_helper.walker_dir_skip_count == 0
        assert stats_helper.walker_file_count == 10
        assert stats_helper.walker_file_skip_count == 0

        assert stats_helper.get_walker_dir_item_count() == 10

    def test_error_handling(self, tmp_path, caplog, capsys):
        hash = hashlib.sha512()
        for no in range(10):
            with Path(tmp_path, f'working_file_{no}.txt').open("wb") as f:
                data = b'X%i' % no
                f.write(data)
                hash.update(data)

        expected_hash = hash.hexdigest()

        src_file = Path(tmp_path, "source_file.txt")
        src_file.touch()

        dst_file = Path(tmp_path, "destination.txt")
        dst_file.symlink_to(src_file)

        # Create a broken symlink, by deleting the source file:
        src_file.unlink()

        # Not readable file:
        Path(tmp_path, "no_read.txt").touch(mode=0o200)

        with caplog.at_level(logging.DEBUG):
            stats_helper = calc_sha512(
                top_path=tmp_path,
                wait=True
            )

        captured_out, captured_err = verbose_get_capsys(capsys)

        stats_helper2assertments(stats_helper)

        if not ON_TRAVIS:
            # FIXME: hash on appveyor.com and local are correct, but not on TravisCI, why?
            assert stats_helper.hash == expected_hash

        assert stats_helper.collect_dir_item_count == 12
        assert stats_helper.collect_file_size == 20
        assert stats_helper.process_file_size == 20
        assert stats_helper.walker_dir_count == 0
        assert stats_helper.walker_dir_skip_count == 0
        assert stats_helper.walker_file_count == 12
        assert stats_helper.walker_file_skip_count == 0

        if sys.platform == 'win32':
            # .touch(mode=0o200) doesn't work on Windows ;)
            assert stats_helper.process_error_count == 0
            assert stats_helper.process_files == 11
        else:
            assert stats_helper.process_error_count == 1
            assert stats_helper.process_files == 10

            assert 'Error processing dir entry' in captured_out
            assert 'PermissionError: [Errno 13] Permission denied:' in captured_out
            assert 'no_read.txt' in captured_out
