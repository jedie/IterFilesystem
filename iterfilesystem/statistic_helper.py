# IterFilesystem
import pprint

from iterfilesystem.constants import (
    COLLECT_COUNT_DONE,
    COLLECT_COUNT_DURATION,
    COLLECT_SIZE_DONE,
    COLLECT_SIZE_DURATION,
    DIR_ITEM_COUNT,
    FILE_SIZE
)


class StatisticHelper:
    def __init__(self):
        # set by ScandirWalker:
        self.walker_dir_count = 0
        self.walker_dir_skip_count = 0

        self.walker_file_count = 0
        self.walker_file_skip_count = 0

        # from collect_count_process:
        self.collect_dir_item_count = 0
        self.collect_dir_item_count_done = False
        self.collect_dir_item_duration = None

        # form collect_size_process:
        self.collect_file_size = 0
        self.collect_file_size_done = False
        self.collect_file_size_duration = None

        # from worker_process:
        self.process_files = 0
        self.process_file_size = 0
        self.process_error_count = 0

    def get_walker_dir_item_count(self):
        return (
            self.walker_dir_count
            + self.walker_dir_skip_count
            + self.walker_file_count
            + self.walker_file_skip_count
        )

    def update_from_scandir_walker(self, scan_dir_walker):
        self.walker_dir_count = scan_dir_walker.stats_helper.walker_dir_count
        self.walker_dir_skip_count = scan_dir_walker.stats_helper.walker_dir_skip_count

        self.walker_file_count = scan_dir_walker.stats_helper.walker_file_count
        self.walker_file_skip_count = scan_dir_walker.stats_helper.walker_file_skip_count

    def update_from_multiprocessing_stats(self, multiprocessing_stats):
        self.collect_dir_item_count = multiprocessing_stats.get(DIR_ITEM_COUNT, 0)
        self.collect_dir_item_count_done = multiprocessing_stats.get(COLLECT_COUNT_DONE, False)
        self.collect_dir_item_duration = multiprocessing_stats.get(COLLECT_COUNT_DURATION, None)

        self.collect_file_size = multiprocessing_stats.get(FILE_SIZE, 0)
        self.collect_file_size_done = multiprocessing_stats.get(COLLECT_SIZE_DONE, False)
        self.collect_file_size_duration = multiprocessing_stats.get(COLLECT_SIZE_DURATION, None)

    def update_from_worker(self, scan_dir_walker, multiprocessing_stats):
        self.update_from_scandir_walker(scan_dir_walker)
        self.update_from_multiprocessing_stats(multiprocessing_stats)

    def update(self, file_size):
        self.process_file_size += file_size

    def items(self):
        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue

            attr = getattr(self, attr_name)
            if callable(attr):
                continue

            yield attr_name, attr

    def pformat(self):
        return pprint.pformat(dict(self.items()))

    def print_stats(self):
        print(self.pformat())

    def done(self):
        """
        Maybe the scan processes terminated before complete: The worker was faster
        So, 'correct' the statistics.
        """
        self.collect_dir_item_count = max(
            self.collect_dir_item_count, self.get_walker_dir_item_count()
        )
        self.collect_file_size = max(
            self.collect_file_size, self.process_file_size
        )
