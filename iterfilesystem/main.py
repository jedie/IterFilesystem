import logging
import sys
import traceback
from multiprocessing import Manager, Process
from timeit import default_timer

# IterFilesystem
from iterfilesystem.constants import (
    COLLECT_COUNT_DONE,
    COLLECT_COUNT_DURATION,
    COLLECT_SIZE_DONE,
    COLLECT_SIZE_DURATION,
    DIR_ITEM_COUNT,
    FILE_SIZE
)
from iterfilesystem.humanize import human_filesize, human_time
from iterfilesystem.process_bar import IterFilesystemProcessBar, Printer
from iterfilesystem.process_priority import set_high_priority, set_low_priority
from iterfilesystem.statistic_helper import StatisticHelper
from iterfilesystem.utils import UpdateInterval

log = logging.getLogger()


class IterFilesystem:
    multiprocessing_stats = None  # will be created in process()

    def __init__(self, *, ScanDirClass, scan_dir_kwargs, update_interval_sec, wait=False):

        self.stats_helper = StatisticHelper()
        self.ScanDirClass = ScanDirClass
        self.scan_dir_kwargs = scan_dir_kwargs

        # fail fast -> check if scan directory exists, before create sub processed:
        self.worker_scan_dir = self._get_scan_dir_instance(verbose=True)

        self.update_interval_sec = update_interval_sec
        self.worker_update_interval = UpdateInterval(interval=self.update_interval_sec)
        self.wait = wait

        # init in self.start()
        self.update_file_interval = None  # status interval for big file processing
        self.low_priority_set = None

    def _get_scan_dir_instance(self, verbose):
        self.scan_dir_kwargs.update(dict(
            verbose=verbose,
            stats_helper=self.stats_helper
        ))
        return self.ScanDirClass(**self.scan_dir_kwargs)

    def _collect_counts(self, multiprocessing_stats):
        log.info('Collect filesystem item process starts')
        set_high_priority()
        scan_dir_walker = self._get_scan_dir_instance(verbose=False)

        update_interval = UpdateInterval(interval=self.update_interval_sec)
        start_time = default_timer()
        for _ in scan_dir_walker:
            if update_interval:
                multiprocessing_stats[DIR_ITEM_COUNT] = \
                    scan_dir_walker.stats_helper.get_walker_dir_item_count()
        duration = default_timer() - start_time

        multiprocessing_stats[DIR_ITEM_COUNT] = \
            scan_dir_walker.stats_helper.get_walker_dir_item_count()
        multiprocessing_stats[COLLECT_COUNT_DONE] = True
        multiprocessing_stats[COLLECT_COUNT_DURATION] = duration

        Printer.write(
            f'Collect filesystem item process done in {human_time(duration)}'
            f' ({scan_dir_walker.stats_helper.get_walker_dir_item_count()} items)'
        )

    def _collect_size(self, multiprocessing_stats):
        log.info('Collect file size process starts')
        set_high_priority()
        collect_file_size = 0
        scan_dir_walker = self._get_scan_dir_instance(verbose=False)

        update_interval = UpdateInterval(interval=self.update_interval_sec)
        start_time = default_timer()
        for dir_entry in scan_dir_walker:
            if dir_entry.is_file(follow_symlinks=False):
                collect_file_size += dir_entry.stat().st_size

            if update_interval:
                multiprocessing_stats[FILE_SIZE] = collect_file_size
        duration = default_timer() - start_time

        multiprocessing_stats[FILE_SIZE] = collect_file_size
        multiprocessing_stats[COLLECT_SIZE_DONE] = True
        multiprocessing_stats[COLLECT_SIZE_DURATION] = duration

        Printer.write(
            f'Collect file size process done in {human_time(duration)}'
            f' ({human_filesize(collect_file_size)})'
        )

    def process(self):
        with Manager() as manager:
            self.multiprocessing_stats = manager.dict()

            collect_size_process = None
            collect_count_process = None

            try:
                collect_count_process = Process(
                    name='collect_count',
                    target=self._collect_counts,
                    args=(self.multiprocessing_stats,)
                )
                collect_count_process.start()

                collect_size_process = Process(
                    name='collect_size',
                    target=self._collect_size,
                    args=(self.multiprocessing_stats,)
                )
                collect_size_process.start()

                set_low_priority()
                self.low_priority_set = True

                start_time = default_timer()
                self.start()
                duration = default_timer() - start_time
                self.stats_helper.process_duration = duration

                if self.wait:
                    # In tests we would like to see all results
                    collect_size_process.join()
                    collect_count_process.join()
                else:
                    # After process all files, the stat processes not needed:
                    collect_size_process.terminate()
                    collect_count_process.terminate()
            except KeyboardInterrupt:
                self.stats_helper.abort = True
                self.stats_helper.process_duration = default_timer() - start_time
                print('\n *** Abort via keyboard interrupt! ***\n', file=sys.stderr)
            finally:
                if collect_size_process is not None:
                    collect_size_process.terminate()

                if collect_count_process is not None:
                    collect_count_process.terminate()

        self.stats_helper.done()
        self.done()
        return self.stats_helper

    def _update_stats_helper(self, dir_entry, process_bars):
        self.stats_helper.update_from_worker(
            scan_dir_walker=self.worker_scan_dir,
            multiprocessing_stats=self.multiprocessing_stats,
        )
        if self.low_priority_set:
            if self.stats_helper.collect_dir_item_count_done and self.stats_helper.collect_file_size_done:
                set_high_priority()
                self.low_priority_set = False

        process_bars.update(self.stats_helper, dir_entry)

    def update(self, dir_entry, file_size, process_bars):
        self.stats_helper.process_files += 1
        self.stats_helper.update(file_size=file_size)
        if self.worker_update_interval:
            self._update_stats_helper(dir_entry, process_bars)

    ##############################################################################################
    # methods to overwrite:

    def start(self):
        log.info('Worker starts')

        self.update_file_interval = UpdateInterval(interval=self.update_interval_sec)
        with IterFilesystemProcessBar() as process_bars:
            for dir_entry in self.worker_scan_dir:
                try:
                    self.process_dir_entry(dir_entry=dir_entry, process_bars=process_bars)
                except OSError:
                    self.stats_helper.process_error_count += 1
                    Printer.write('\n'.join([
                        '=' * 100,
                        f'Error processing dir entry: {dir_entry.path}',
                        ' -' * 50,
                        traceback.format_exc().rstrip(),
                        '=' * 100,
                    ]))

                if self.worker_update_interval:
                    self._update_stats_helper(dir_entry, process_bars)

            self._update_stats_helper(dir_entry, process_bars)
        log.info('Worker done.')

    def process_dir_entry(self, dir_entry, process_bars):
        """
        The implementation must update the total file size, see below:
        """
        # e.g.:
        self.update(
            dir_entry=dir_entry,
            file_size=dir_entry.stat().st_size,
            process_bars=process_bars
        )
        raise NotImplementedError()

    def done(self):
        """
        Will be called after all dir items are processed
        """
        pass
