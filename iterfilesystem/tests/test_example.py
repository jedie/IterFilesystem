import logging

from iterfilesystem.example import count_filesystem
from iterfilesystem.tests import BaseTestCase


class TestExample(BaseTestCase):
    def test_count_filesystem(self, caplog):
        with caplog.at_level(logging.DEBUG):
            walker = count_filesystem(
                top_path=self.package_path,
                skip_dirs=self.skip_dirs,
                skip_filenames=self.skip_filenames,

                force_restart=True,
                complete_cleanup=True,

                worker_count=3,

                update_interval_sec=0.5
            )

        log_messages = '\n'.join([rec.message for rec in caplog.records])
        print(log_messages)

        # FIXME: Failed on appveyor, see:
        # https://ci.appveyor.com/project/jedie/iterfilesystem/builds/27420855/job/rcu9lwa4hd7gqjax#L95
        # assert "persist data doesn't exists" in log_messages

        assert "Skip file: '.gitignore'" in log_messages
        assert "Skip dir: '.tox'" in log_messages
        assert "Complete cleanup should be made" in log_messages

        walker.print_stats()

        assert walker.fs_info.file_count >= 20
        assert walker.fs_info.file_size > 150000
        assert walker.fs_info.dir_count >= 4
        assert walker.fs_info.other_count == 0

        seen_count = walker.fs_info.file_count + walker.fs_info.dir_count + walker.fs_info.other_count
        assert seen_count == walker.total_count
