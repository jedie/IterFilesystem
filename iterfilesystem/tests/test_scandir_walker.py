import os
from pathlib import Path

# IterFilesystem
from iterfilesystem.iter_scandir import ScandirWalker
from iterfilesystem.statistics import Statistics
from iterfilesystem.tests import BaseTestCase


class TestScanDirWalk(BaseTestCase):
    def test_hash(self, tmp_path):
        for no in range(10):
            os.makedirs(Path(tmp_path, 'one'), exist_ok=True)
            Path(tmp_path, 'one', 'one.txt').touch()

            os.makedirs(Path(tmp_path, 'two'), exist_ok=True)
            Path(tmp_path, 'two', 'two.txt').touch()

            Path(tmp_path, 'skip1.foo').touch()
            Path(tmp_path, 'skip2.bar').touch()

        statistics = Statistics()

        sw = ScandirWalker(
            top_path=tmp_path,
            statistics=statistics,
            skip_dir_patterns=(),
            skip_file_patterns=(),
            verbose=True
        )
        names = sorted([dir_item.name for dir_item in sw])

        statistics.print_stats()

        assert names == ['one', 'one.txt', 'skip1.foo', 'skip2.bar', 'two', 'two.txt']

        assert statistics.dir_count == 2
        assert statistics.file_count == 4
        assert statistics.skip_dir_count == 0
        assert statistics.skip_file_count == 0

        print('*' * 100)

        statistics = Statistics()

        sw = ScandirWalker(
            top_path=tmp_path,
            statistics=statistics,
            skip_dir_patterns=(),
            skip_file_patterns=('*.foo', '*.b?r'),
            verbose=True
        )
        names = sorted([dir_item.name for dir_item in sw])

        statistics.print_stats()

        assert names == ['one', 'one.txt', 'two', 'two.txt']

        assert statistics.dir_count == 2
        assert statistics.file_count == 2
        assert statistics.skip_dir_count == 0
        assert statistics.skip_file_count == 2

        print('*' * 100)

        statistics = Statistics()

        sw = ScandirWalker(
            top_path=tmp_path,
            statistics=statistics,
            skip_dir_patterns=('o?e', 't*'),
            skip_file_patterns=(),
            verbose=True
        )
        names = sorted([dir_item.name for dir_item in sw])

        statistics.print_stats()

        assert names == ['skip1.foo', 'skip2.bar']

        assert statistics.dir_count == 0
        assert statistics.file_count == 2
        assert statistics.skip_dir_count == 2
        assert statistics.skip_file_count == 0
