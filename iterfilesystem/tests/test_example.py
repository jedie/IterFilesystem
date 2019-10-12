import hashlib
import logging
from pathlib import Path

import pytest

# IterFilesystem
from iterfilesystem.example import calc_sha512
from iterfilesystem.tests import BaseTestCase
from iterfilesystem.tests.test_utils import verbose_get_capsys


class TestExample(BaseTestCase):
    def test_package_path(self, caplog, capsys):
        with caplog.at_level(logging.DEBUG):
            statistics = calc_sha512(
                top_path=self.package_path,
                skip_dir_patterns=self.skip_dir_patterns,
                skip_file_patterns=self.skip_file_patterns,
                wait=True
            )

        captured_out, captured_err = verbose_get_capsys(capsys)
        assert 'SHA515 hash calculated over all file content:' in captured_out
        assert 'Total file size:' in captured_out

        log_messages = '\n'.join([rec.message for rec in caplog.records])
        print('_' * 100)
        print('Captured logs:')
        print(log_messages)
        print('-' * 100)

        statistics.print_stats()

        assert statistics.total_dir_item_count >= 40
        assert statistics.dir_item_count >= 40
        assert statistics.total_file_size > 55000
        assert statistics.total_file_size_processed > 55000

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

        statistics = calc_sha512(
            top_path=tmp_path
        )

        statistics.print_stats()

        assert statistics.hash == expected_hash

        assert statistics.total_dir_item_count == 10
        assert statistics.dir_item_count == 10
        assert statistics.total_file_size == 20
        assert statistics.total_file_size_processed == 20
