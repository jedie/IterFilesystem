# IterFilesystem
from iterfilesystem.constants import (
    COLLECT_COUNT_DONE,
    COLLECT_SIZE_DONE,
    DIR_ITEM_COUNT,
    FILE_SIZE
)


class Statistics:
    def __init__(self):
        # set by ScandirWalker:
        self.dir_item_count = 0

        self.dir_count = 0
        self.skip_dir_count = 0
        self.processed_dirs = 0

        self.file_count = 0
        self.skip_file_count = 0
        self.processed_files = 0

        # from collect_counts_process:
        self.total_dir_item_count = 0
        self.collect_dir_item_count_done = False

        # form collect_size_process:
        self.total_file_size = 0
        self.collect_file_size_done = False

        # from worker_process:
        self.total_file_size_processed = 0

    def update_from_scandir_walker(self, scan_dir_walker):
        self.dir_item_count = scan_dir_walker.statistics.dir_item_count
        self.dir_count = scan_dir_walker.statistics.dir_count
        self.skip_dir_count = scan_dir_walker.statistics.skip_dir_count
        self.processed_dirs = scan_dir_walker.statistics.processed_dirs
        self.file_count = scan_dir_walker.statistics.file_count
        self.skip_file_count = scan_dir_walker.statistics.skip_file_count
        self.processed_files = scan_dir_walker.statistics.processed_files

    def update_from_multiprocessing_stats(self, multiprocessing_stats):
        self.total_dir_item_count = multiprocessing_stats.get(DIR_ITEM_COUNT, 0)
        self.collect_dir_item_count_done = multiprocessing_stats.get(COLLECT_COUNT_DONE, False)
        self.total_file_size = multiprocessing_stats.get(FILE_SIZE, 0)
        self.collect_file_size_done = multiprocessing_stats.get(COLLECT_SIZE_DONE, False)

    def update_from_worker(self, scan_dir_walker, multiprocessing_stats):
        self.update_from_scandir_walker(scan_dir_walker)
        self.update_from_multiprocessing_stats(multiprocessing_stats)

    def update(self, file_size):
        self.total_file_size_processed += file_size

    def pformat(self):
        parts = []
        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue

            attr = getattr(self, attr_name)
            if callable(attr):
                continue

            parts.append(
                f'{attr_name}: {attr}'
            )

        return "\n".join(parts)

    def print_stats(self):
        print(self.pformat())

    def done(self):
        """
        Maybe the scan processes terminated before complete: The worker was faster
        So, 'correct' the statistics.
        """
        self.total_dir_item_count = max(self.total_dir_item_count, self.dir_item_count)
        self.total_file_size = max(self.total_file_size, self.total_file_size_processed)
