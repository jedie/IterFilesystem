"""
    Top-level package for iterfilesystem.
"""

import logging
import shutil
import sys
import threading
import time

# https://github.com/peter-wangxu/persist-queue
from persistqueue import Empty
from persistqueue.sqlackqueue import AckStatus, UniqueAckQ

# https://github.com/tqdm/tqdm
from tqdm import tqdm  # https://github.com/tqdm/tqdm

# IterFilesystem
from iterfilesystem.humanize import human_time
from iterfilesystem.utils import (
    get_persist_temp_path,
    left_shorten,
)

__author__ = 'Jens Diemer'
__email__ = 'python@jensdiemer.de'
__version__ = '0.2.0'


def get_module_version():
    return __version__


log = logging.getLogger()


class ThreadedFilesystemWalker:
    queue_get_timeout = 0.5
    total_count = 0
    new_processed_count = 0
    lock = threading.Lock()

    def __init__(
            self,
            *,
            scandir_walker,
            force_restart=False,
            complete_cleanup=True,
            worker_count=3,
            skip_dirs=(),
            update_interval_sec=0.5):

        self.scandir_walker = scandir_walker
        self.worker_count = worker_count
        self.skip_dirs = skip_dirs
        self.update_interval_sec = update_interval_sec

        if not self.scandir_walker.top_path.is_dir():
            raise AssertionError(
                f'Given path {self.scandir_walker.top_path} is not a existing directory!'
            )

        self.persist_path = get_persist_temp_path(seed=str(self.scandir_walker.top_path))
        log.info('Save persist queue to: %s', self.persist_path)

        if force_restart:
            print('Force restart, by delete old persist queue data.')
            self._remove_persist_data()

        self.complete_cleanup = complete_cleanup

        self.queue = UniqueAckQ(path=self.persist_path, multithreading=True)

        # https://github.com/peter-wangxu/persist-queue#example-usage-of-sqlite3-based-sqliteackqueue
        self.ack_status2func = {
            AckStatus.acked: self.queue.ack,  # mark item as acked
            AckStatus.ready: self.queue.nack,  # mark item as ready, so that it can be proceeded again by any worker
            AckStatus.ack_failed: self.queue.ack_failed,  # mark item as `ack_failed` to discard this item
        }

        self.initial_queue_size = self.queue.size
        self.resumed_processed_count = self.queue.acked_count()
        self.failed_count = self.queue.ack_failed_count()

        log.debug('initial queue size............: %s', self.initial_queue_size)
        log.debug('initial queue unack count.....: %s', self.queue.unack_count())
        log.debug('initial queue acked count.....: %s', self.resumed_processed_count)
        log.debug('initial queue ready count.....: %s', self.queue.ready_count())
        log.debug('initial queue ack failed count: %s', self.failed_count)

        self.process_bar = None  # tqdm instance made in self.scandir()

    ##############################################################################################
    # These methods should be overwritten:

    def process_path_item(self, path):
        raise NotImplementedError

    def on_skip(self, dir_entry):
        print(f'\rSkip: {dir_entry}')

    ##############################################################################################

    def scandir(self):
        if self.initial_queue_size > 0:
            print(
                f'*** Resuming {self.initial_queue_size} filesystem items from previous run! ***'
            )
            initial_tqdm = self.initial_queue_size
        else:
            initial_tqdm = int(9e9)

        self.process_bar = tqdm(total=initial_tqdm, miniters=1, dynamic_ncols=True)
        self._set_next_update()
        start_time = time.time()
        try:
            worker_threads = self._start_worker_threads()
            self._start_filesystem_scan()
            self._wait_for_worker_threads(worker_threads)

            duration = time.time() - start_time
        except KeyboardInterrupt:
            with self.lock:
                self._close_process_bar('*** Abort by keyboard interrupt ***')
                raise KeyboardInterrupt
        else:
            total_processed = self.resumed_processed_count + self.new_processed_count + self.failed_count
            missing_items = self.total_count - total_processed

            if missing_items > 0:
                print(f'\r\n*** ERROR: {missing_items} item(s) not processed! ***', file=sys.stderr)
                self._close_process_bar(f'*** {missing_items} missing item(s) ***')
            else:
                if self.failed_count > 0:
                    print(f'\r\n*** {self.failed_count} item(s) failed! ***', file=sys.stderr)
                    self._close_process_bar(f'*** {self.failed_count} failed item(s) ***')
                else:
                    self._close_process_bar('*** all items processed ***')

                if self.complete_cleanup:
                    log.debug('Complete cleanup should be made...')
                    del self.queue  # needed for windows to rmtree the sqlite files ;)
                    try:
                        self._remove_persist_data()
                    except PermissionError as err:
                        log.exception("Can't remove persistent data: %s", err)
                        # FIXME: Under windows we get:
                        # The process cannot access the file because it is being used by another process
                        # See: https://github.com/peter-wangxu/persist-queue/issues/110

            print(f'total filesystem items: {self.total_count}')
            if self.resumed_processed_count:
                print(f'Previous finished.....: {self.resumed_processed_count}')
                print(f'New processed items...: {self.new_processed_count}')
            print(f'Finish in.............: {human_time(duration)}.')

    def _update_process_bar(self, text):
        self.process_bar.total = self.total_count
        self.process_bar.n = self.resumed_processed_count + self.new_processed_count
        self.process_bar.set_description(text)

    def _close_process_bar(self, text):
        self._update_process_bar(text)
        self.process_bar.close()
        print()

    def _remove_persist_data(self):
        if not self.persist_path.exists():
            log.debug("persist data doesn't exists: %s", self.persist_path)
        else:
            print(f'Remove persist data: {self.persist_path}')
            shutil.rmtree(self.persist_path)

    def _set_next_update(self):
        self.next_update = time.time() + self.update_interval_sec

    def _worker(self, thread_no):
        while True:
            try:
                path = self.queue.get(block=True, timeout=self.queue_get_timeout)
            except Empty:
                self._update_process_bar(f'{thread_no:02} worker thread empty')
                return

            ack_status = self.process_path_item(path=path)
            if ack_status == AckStatus.ack_failed:
                with self.lock:
                    print(f'ERROR with {path}', file=sys.stderr)
                    self.failed_count += 1

            try:
                ack_func = self.ack_status2func[ack_status]
            except KeyError:
                if ack_status is None:
                    raise AssertionError('no ACK status returned!')
                else:
                    raise AssertionError(f'unknown ACK status returned: {ack_status!r}')

            # set ACK status:
            ack_func(path)  # call e.g.: self.queue.ack(path)

            with self.lock:
                self.new_processed_count += 1

                if time.time() > self.next_update:
                    cut_path = left_shorten(text=path, width=40, placeholder='...')
                    self._update_process_bar(f'{thread_no:02} {cut_path}')
                    self._set_next_update()

    def _start_worker_threads(self):
        log.debug('start %i worker threads', self.worker_count)
        worker_threads = []
        for thread_no in range(self.worker_count):
            thread = threading.Thread(
                target=self._worker,
                name=f'{thread_no:02}',
                kwargs={'thread_no': thread_no},
                daemon=True,
            )
            thread.start()
            worker_threads.append(thread)
        return worker_threads

    def _wait_for_worker_threads(self, worker_threads):
        for thread in worker_threads:
            # log.debug('wait for thread %s to complete...', thread.getName())
            thread.join()
            # log.debug('thread %s ended.', thread.getName())

    def _start_filesystem_scan(self):
        log.debug('Start filesystem scan...')
        start_time = time.time()

        for dir_entry in self.scandir_walker:
            self.queue.put(dir_entry.path)
            with self.lock:
                self.total_count += 1

        duration = time.time() - start_time
        print(f'\rRead filesystem with {self.total_count} items in {human_time(duration)}.')
