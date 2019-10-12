import hashlib
import logging
from pathlib import Path

# IterFilesystem
import pytest

from iterfilesystem.example import calc_sha512
from iterfilesystem.tests import BaseTestCase
from iterfilesystem.tests.test_utils import verbose_get_capsys


class TestExample(BaseTestCase):
    def test_package_path(self, caplog, capsys):
        with caplog.at_level(logging.DEBUG):
            statistics = calc_sha512(
                top_path=self.package_path,
                skip_dirs=self.skip_dirs,
                skip_filenames=self.skip_filenames,
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
    #
    # def test_error_handling(self, tmp_path, caplog, capsys):
    #     for no in range(10):
    #         with Path(tmp_path, f'working_file_{no}.txt').open("w") as f:
    #             f.write(f'X{no}')
    #
    #     src_file = Path(tmp_path, "source_file.txt")
    #     src_file.touch()
    #
    #     dst_file = Path(tmp_path, "destination.txt")
    #     dst_file.symlink_to(src_file)
    #
    #     # Create a broken symlink, by deleting the source file:
    #     src_file.unlink()
    #
    #     with caplog.at_level(logging.DEBUG):
    #         walker = count_filesystem(top_path=tmp_path)
    #
    #     captured = capsys.readouterr()
    #     print(captured.out)
    #
    #     walker.print_stats()
    #
    #     assert 'Read filesystem with 11 items' in captured.out
    #
    #     assert walker.fs_info.file_count == 10
    #     assert walker.fs_info.file_size == 20
    #     assert walker.fs_info.dir_count == 0
    #     assert walker.fs_info.other_count == 1  # the broken symlink
    #
    #     seen_count = walker.fs_info.file_count + walker.fs_info.dir_count + walker.fs_info.other_count
    #     assert seen_count == walker.total_count
