import os
from pathlib import Path

# IterFilesystem
from iterfilesystem.iter_scandir import ScandirWalker
from iterfilesystem.statistic_helper import StatisticHelper
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

        stats_helper = StatisticHelper()

        sw = ScandirWalker(
            top_path=tmp_path,
            stats_helper=stats_helper,
            skip_dir_patterns=(),
            skip_file_patterns=(),
            verbose=True
        )
        names = sorted([dir_item.name for dir_item in sw])

        stats_helper.print_stats()

        assert names == ['one', 'one.txt', 'skip1.foo', 'skip2.bar', 'two', 'two.txt']

        assert stats_helper.walker_dir_count == 2
        assert stats_helper.walker_file_count == 4
        assert stats_helper.walker_dir_skip_count == 0
        assert stats_helper.walker_file_skip_count == 0

        print('*' * 100)

        stats_helper = StatisticHelper()

        sw = ScandirWalker(
            top_path=tmp_path,
            stats_helper=stats_helper,
            skip_dir_patterns=(),
            skip_file_patterns=('*.foo', '*.b?r'),
            verbose=True
        )
        names = sorted([dir_item.name for dir_item in sw])

        stats_helper.print_stats()

        assert names == ['one', 'one.txt', 'two', 'two.txt']

        assert stats_helper.walker_dir_count == 2
        assert stats_helper.walker_file_count == 2
        assert stats_helper.walker_dir_skip_count == 0
        assert stats_helper.walker_file_skip_count == 2

        print('*' * 100)

        stats_helper = StatisticHelper()

        sw = ScandirWalker(
            top_path=tmp_path,
            stats_helper=stats_helper,
            skip_dir_patterns=('o?e', 't*'),
            skip_file_patterns=(),
            verbose=True
        )
        names = sorted([dir_item.name for dir_item in sw])

        stats_helper.print_stats()

        assert names == ['skip1.foo', 'skip2.bar']

        assert stats_helper.walker_dir_count == 0
        assert stats_helper.walker_file_count == 2
        assert stats_helper.walker_dir_skip_count == 2
        assert stats_helper.walker_file_skip_count == 0
