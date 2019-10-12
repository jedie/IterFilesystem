import logging
import multiprocessing
from multiprocessing import Manager, Process
from timeit import default_timer

# IterFilesystem
from iterfilesystem.constants import (
    COLLECT_COUNT_DONE,
    COLLECT_SIZE_DONE,
    DIR_ITEM_COUNT,
    FILE_SIZE
)
from iterfilesystem.humanize import human_filesize, human_time
from iterfilesystem.process_bar import FilesystemWorkerProcessBar, Printer
from iterfilesystem.statistics import Statistics
from iterfilesystem.utils import UpdateInterval

log = logging.getLogger()


class FilesystemWorker:
    def __init__(
            self,
            *,
            ScanDirClass,
            scan_dir_kwargs,
            WorkerClass,
            update_interval_sec,
            wait=False):
        scan_dir_kwargs.update(dict(
            statistics=Statistics()
        ))

        # fail fast -> check if scan directory exists, before create sub processed:
        ScanDirClass(**scan_dir_kwargs, verbose=True)

        self.ScanDirClass = ScanDirClass
        self.scan_dir_kwargs = scan_dir_kwargs
        self.WorkerClass = WorkerClass
        self.update_interval_sec = update_interval_sec
        self.wait = wait

    def get_scan_dir_instance(self, verbose):
        self.scan_dir_kwargs.update(dict(
            verbose=verbose,
        ))
        return self.ScanDirClass(**self.scan_dir_kwargs)

    def collect_counts(self, multiprocessing_stats):
        log.info('Collect filesystem item process starts')
        scan_dir_walker = self.get_scan_dir_instance(verbose=False)

        update_interval = UpdateInterval(interval=self.update_interval_sec)
        start_time = default_timer()
        for _ in scan_dir_walker:
            if update_interval:
                multiprocessing_stats[DIR_ITEM_COUNT] = scan_dir_walker.statistics.dir_item_count
        duration = default_timer() - start_time

        multiprocessing_stats[DIR_ITEM_COUNT] = scan_dir_walker.statistics.dir_item_count
        multiprocessing_stats[COLLECT_COUNT_DONE] = True

        Printer.write(
            f'Collect filesystem item process done in {human_time(duration)}'
            f' ({scan_dir_walker.statistics.dir_item_count} items)'
        )

    def collect_size(self, multiprocessing_stats):
        log.info('Collect file size process starts')
        total_file_size = 0
        scan_dir_walker = self.get_scan_dir_instance(verbose=False)

        update_interval = UpdateInterval(interval=self.update_interval_sec)
        start_time = default_timer()
        for dir_entry in scan_dir_walker:
            if dir_entry.is_file(follow_symlinks=False):
                total_file_size += dir_entry.stat().st_size

            if update_interval:
                multiprocessing_stats[FILE_SIZE] = total_file_size
        duration = default_timer() - start_time

        multiprocessing_stats[FILE_SIZE] = total_file_size
        multiprocessing_stats[COLLECT_SIZE_DONE] = True

        Printer.write(
            f'Collect file size process done in {human_time(duration)}'
            f' ({human_filesize(total_file_size)})'
        )

    def process(self):
        stats_queue = multiprocessing.SimpleQueue()
        with Manager() as manager:
            multiprocessing_stats = manager.dict()

            worker_process = Process(
                target=build_worker,
                kwargs=dict(
                    ScanDirClass=self.ScanDirClass,
                    scan_dir_kwargs=self.scan_dir_kwargs,
                    WorkerClass=self.WorkerClass,
                    stats_queue=stats_queue,
                    multiprocessing_stats=multiprocessing_stats,
                    update_interval_sec=self.update_interval_sec,
                )
            )
            worker_process.start()

            collect_counts_process = Process(
                target=self.collect_counts,
                args=(multiprocessing_stats,)
            )
            collect_counts_process.start()

            collect_size_process = Process(
                target=self.collect_size,
                args=(multiprocessing_stats,)
            )
            collect_size_process.start()

            worker_process.join()

            if self.wait:
                # In tests we would like to see all results
                collect_size_process.join()
                collect_counts_process.join()
            else:
                # After process all files, the stat processes not needed:
                collect_size_process.terminate()
                collect_counts_process.terminate()

        statistics = stats_queue.get()  # get statistics from worker process
        return statistics


class FilesystemBaseWorker:
    def __init__(
            self,
            *,
            process_bar,
            scan_dir_walker,
            stats_queue,
            multiprocessing_stats,
            update_interval_sec):
        self._process_bar = process_bar
        self.scan_dir_walker = scan_dir_walker
        self.stats_queue = stats_queue
        self.multiprocessing_stats = multiprocessing_stats
        self.update_interval_sec = update_interval_sec
        self._update_interval = UpdateInterval(interval=self.update_interval_sec)

        self.statistics = Statistics()

    def _update_statistics(self, dir_entry):
        self.statistics.update_from_worker(
            scan_dir_walker=self.scan_dir_walker,
            multiprocessing_stats=self.multiprocessing_stats,
        )
        self._process_bar.update(self.statistics, dir_entry)

    def update(self, dir_entry, file_size):
        self.statistics.update(file_size=file_size)
        if self._update_interval:
            self._update_statistics(dir_entry)

    def start(self):
        log.info('Worker starts')

        for dir_entry in self.scan_dir_walker:
            self.process(dir_entry=dir_entry)

            if self._update_interval:
                self._update_statistics(dir_entry)

        self._update_statistics(dir_entry)

        log.info('Worker done.')

    ##############################################################################################
    # methods to overwrite:

    def process(self, dir_entry):
        """
        The implementation must update the total file size, e.g.:

            self.update(dir_entry=dir_entry, file_size=dir_entry.stat().st_size)
        """
        raise NotImplementedError()

    def done(self):
        """
        transfer statistics from worker process to main process

        Can be overwritten but should be called via super() ;)
        """
        self.statistics.done()
        self.stats_queue.put(self.statistics)


def build_worker(*, ScanDirClass,
                 scan_dir_kwargs,
                 WorkerClass,
                 stats_queue,
                 multiprocessing_stats,
                 update_interval_sec):

    scan_dir_kwargs.update(dict(
        verbose=True,
        statistics=Statistics()
    ))

    with FilesystemWorkerProcessBar() as process_bar:
        worker = WorkerClass(
            process_bar=process_bar,
            scan_dir_walker=ScanDirClass(**scan_dir_kwargs),
            stats_queue=stats_queue,
            multiprocessing_stats=multiprocessing_stats,
            update_interval_sec=update_interval_sec,
        )
        worker.start()
    worker.done()
