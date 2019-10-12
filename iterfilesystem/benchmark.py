#!/usr/bin/env python3
import hashlib
import logging
import os
import time
from pathlib import Path

# https://github.com/peter-wangxu/persist-queue
from persistqueue.sqlackqueue import AckStatus

# https://github.com/tqdm/tqdm
from tqdm import tqdm

# IterFilesystem
from iterfilesystem import ThreadedFilesystemWalker
from iterfilesystem.iter_scandir import ScandirWalker

log = logging.getLogger()


class Hasher:
    def __init__(self, block_size=10 * 1024):
        self.block_size = block_size
        self.file_hash = hashlib.sha512()

    def update(self, path):
        with path.open('rb') as f:
            while True:
                fb = f.read(self.block_size)
                if not fb:
                    break
                self.file_hash.update(fb)

    def hexdigest(self):
        return self.file_hash.hexdigest()


class CountFilesystemWalker(ThreadedFilesystemWalker):
    def __init__(self, *args, **kwargs):
        self.file_count = 0
        self.file_size = 0
        self.dir_count = 0
        self.other_count = 0
        self.hasher = Hasher()
        super().__init__(*args, **kwargs)

    def process_path_item(self, path):
        try:
            fs_item = Path(path)
            with self.lock:
                if fs_item.is_dir():
                    self.dir_count += 1
                elif fs_item.is_file():
                    self.hasher.update(fs_item)
                    self.file_size += fs_item.stat().st_size
                    self.file_count += 1
                else:
                    self.other_count += 1
        except OSError:
            log.exception('error process path item')
            return AckStatus.ack_failed
        else:
            return AckStatus.acked

    def print_stats(self):
        print(f'File count.....: {self.file_count} with {self.file_size} Bytes')
        print(f'Directory count: {self.dir_count}')
        print(f'Other count....: {self.other_count}')
        print(f'Hash over all files is: {self.hasher.hexdigest()}')

        seen_count = self.file_count + self.dir_count + self.other_count
        if seen_count != self.total_count:
            print("NOTE: not all collected!")


def count_filesystem(top_path, skip_dirs=(), skip_filenames=(), **kwargs):
    scandir_walker = ScandirWalker(
        top_path=Path(top_path).expanduser(),
        skip_dirs=skip_dirs,
        skip_filenames=skip_filenames,
    )
    walker = CountFilesystemWalker(scandir_walker=scandir_walker, **kwargs)

    try:
        walker.scandir()
    except KeyboardInterrupt:
        pass  # print stats after Strg-C

    return walker


class NoThreadsCountFilesystemWalker:
    def __init__(self, top_path, skip_dirs=(), skip_filenames=()):
        self.process_bar = tqdm(miniters=1, dynamic_ncols=True)
        self.scandir_walker = ScandirWalker(
            top_path=Path(top_path).expanduser(),
            skip_dirs=skip_dirs,
            skip_filenames=skip_filenames,
        )
        self.total_count = 0
        self.file_count = 0
        self.file_size = 0
        self.dir_count = 0
        self.other_count = 0
        self.hasher = Hasher()

    def scandir(self):
        for item in self.scandir_walker:
            self.process_path_item(item)
            self.process_bar.update(1)
            self.total_count += 1
        self.process_bar.close()

    def process_path_item(self, path):
        try:
            fs_item = Path(path)
            if fs_item.is_dir():
                self.dir_count += 1
            elif fs_item.is_file():
                self.hasher.update(fs_item)
                self.file_size += fs_item.stat().st_size
                self.file_count += 1
            else:
                self.other_count += 1
        except OSError:
            log.exception('error process path item')

    def print_stats(self):
        print(f'File count.....: {self.file_count} with {self.file_size} Bytes')
        print(f'Directory count: {self.dir_count}')
        print(f'Other count....: {self.other_count}')
        print(f'Hash over all files is: {self.hasher.hexdigest()}')

        seen_count = self.file_count + self.dir_count + self.other_count
        if seen_count != self.total_count:
            print("NOTE: not all collected!")


class TwoSteps:
    def __init__(self, top_path, skip_dirs=(), skip_filenames=()):
        self.top_path = top_path
        self.skip_dirs = skip_dirs
        self.skip_filenames = skip_filenames

        self.total_count = 0
        self.file_count = 0
        self.file_size = 0
        self.dir_count = 0
        self.other_count = 0
        self.hasher = Hasher()

    def scandir(self):
        total_count = self.calculate_count()
        for item in tqdm(self.get_walker(), total=total_count):
            self.process_path_item(item)
            self.total_count += 1

    def process_path_item(self, path):
        try:
            fs_item = Path(path)
            if fs_item.is_dir():
                self.dir_count += 1
            elif fs_item.is_file():
                self.hasher.update(fs_item)
                self.file_size += fs_item.stat().st_size
                self.file_count += 1
            else:
                self.other_count += 1
        except OSError:
            log.exception('error process path item')

    def print_stats(self):
        print(f'File count.....: {self.file_count} with {self.file_size} Bytes')
        print(f'Directory count: {self.dir_count}')
        print(f'Other count....: {self.other_count}')
        print(f'Hash over all files is: {self.hasher.hexdigest()}')

        seen_count = self.file_count + self.dir_count + self.other_count
        if seen_count != self.total_count:
            print("NOTE: not all collected!")

    def get_walker(self):
        return ScandirWalker(
            top_path=Path(self.top_path).expanduser(),
            skip_dirs=self.skip_dirs,
            skip_filenames=self.skip_filenames,
        )

    def calculate_count(self):
        walker = self.get_walker()
        return len(tuple(tqdm(walker)))


class ThreeSteps:
    def __init__(self, top_path, skip_dirs=(), skip_filenames=()):
        self.top_path = top_path
        self.skip_dirs = skip_dirs
        self.skip_filenames = skip_filenames

        self.total_count = 0
        self.file_count = 0
        self.file_size = 0
        self.dir_count = 0
        self.other_count = 0
        self.hasher = Hasher()

    def scandir(self):
        self.total_count = self.calculate_count()
        self.file_size = self.calculate_file_size()

        self.process_bar = tqdm(total=self.file_size, unit="B", unit_scale=True)
        for item in self.get_walker():
            self.process_path_item(item)

    def process_path_item(self, path):
        try:
            fs_item = Path(path)
            if fs_item.is_dir():
                self.dir_count += 1
            elif fs_item.is_file():
                self.hasher.update(fs_item)
                self.process_bar.update(fs_item.stat().st_size)
                self.file_count += 1
            else:
                self.other_count += 1
        except OSError:
            log.exception('error process path item')

    def print_stats(self):
        print(f'File count.....: {self.file_count} with {self.file_size} Bytes')
        print(f'Directory count: {self.dir_count}')
        print(f'Other count....: {self.other_count}')
        print(f'Hash over all files is: {self.hasher.hexdigest()}')

        seen_count = self.file_count + self.dir_count + self.other_count
        if seen_count != self.total_count:
            print("NOTE: not all collected!")

    def get_walker(self):
        return ScandirWalker(
            top_path=Path(self.top_path).expanduser(),
            skip_dirs=self.skip_dirs,
            skip_filenames=self.skip_filenames,
        )

    def calculate_count(self):
        walker = self.get_walker()
        return len(tuple(tqdm(walker)))

    def calculate_file_size(self):
        file_size = 0
        for item in tqdm(self.get_walker(), total=self.total_count):
            if item.is_file(follow_symlinks=False):
                file_size += item.stat().st_size
        return file_size


class TwoSteps2:
    def __init__(self, top_path, skip_dirs=(), skip_filenames=()):
        self.top_path = top_path
        self.skip_dirs = skip_dirs
        self.skip_filenames = skip_filenames

        self.total_count = 0
        self.file_count = 0
        self.file_size = 0
        self.dir_count = 0
        self.other_count = 0
        self.hasher = Hasher()

    def scandir(self):
        for item in tqdm(self.get_walker()):
            self.total_count += 1
            if item.is_file(follow_symlinks=False):
                self.file_size += item.stat().st_size

        self.process_bar = tqdm(total=self.file_size, unit="B", unit_scale=True)
        for item in self.get_walker():
            self.process_path_item(item)

    def process_path_item(self, path):
        try:
            fs_item = Path(path)
            if fs_item.is_dir():
                self.dir_count += 1
            elif fs_item.is_file():
                self.hasher.update(fs_item)
                self.process_bar.update(fs_item.stat().st_size)
                self.file_count += 1
            else:
                self.other_count += 1
        except OSError:
            log.exception('error process path item')

    def print_stats(self):
        print(f'File count.....: {self.file_count} with {self.file_size} Bytes')
        print(f'Directory count: {self.dir_count}')
        print(f'Other count....: {self.other_count}')
        print(f'Hash over all files is: {self.hasher.hexdigest()}')

        seen_count = self.file_count + self.dir_count + self.other_count
        if seen_count != self.total_count:
            print("NOTE: not all collected!")

    def get_walker(self):
        return ScandirWalker(
            top_path=Path(self.top_path).expanduser(),
            skip_dirs=self.skip_dirs,
            skip_filenames=self.skip_filenames,
        )


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.CRITICAL
        # level=logging.INFO
        # level=logging.DEBUG
    )

    start_time = time.time()

    # walker = count_filesystem(
    #     # top_path='~/bin',
    #     top_path='~/Sync',
    #     # File count.....: 7776 with 7502514116 Bytes
    #     # Directory count: 298
    #     # Other count....: 0
    #     # Hash over all files is: 452e0bfd5013d672121605e8fabb28c7db8e09fb2dd5bed12c5aa8d1932a12dd5f98d214c361e2e8d88ac0b95c24633d20b121a96c48c52c238377b7269bd97c
    #     #  *** Duration: 33.71sec.
    #     skip_dirs=('.config', '.local'),
    #     skip_filenames=('meld', 'aw-qt'),
    #
    #     force_restart=True,
    #     complete_cleanup=True,
    #     worker_count=3,
    #     update_interval_sec=0.5
    # )
    # walker.print_stats()

    # walker = NoThreadsCountFilesystemWalker(
    #     # top_path='~/bin',
    #     top_path='~/Sync',
    #     # File count.....: 7776 with 7502514116 Bytes
    #     # Directory count: 298
    #     # Other count....: 0
    #     # Hash over all files is: 452e0bfd5013d672121605e8fabb28c7db8e09fb2dd5bed12c5aa8d1932a12dd5f98d214c361e2e8d88ac0b95c24633d20b121a96c48c52c238377b7269bd97c
    #     #  *** Duration: 11.68sec.
    #
    #     skip_dirs=('.config', '.local'),
    #     skip_filenames=('meld', 'aw-qt'),
    # )
    # walker.scandir()
    # walker.print_stats()

    # walker = TwoSteps(
    #     # top_path='~/bin',
    #     top_path='~/Sync',
    #     # File count.....: 7776 with 7502514116 Bytes
    #     # Directory count: 298
    #     # Other count....: 0
    #     # Hash over all files is: 452e0bfd5013d672121605e8fabb28c7db8e09fb2dd5bed12c5aa8d1932a12dd5f98d214c361e2e8d88ac0b95c24633d20b121a96c48c52c238377b7269bd97c
    #     #  *** Duration: 11.61sec.
    #
    #     skip_dirs=('.config', '.local'),
    #     skip_filenames=('meld', 'aw-qt'),
    # )
    # walker.scandir()
    # walker.print_stats()

    # walker = ThreeSteps(
    #     # top_path='~/bin',
    #     top_path='~/Sync',
    #     # File count.....: 7776 with 15005028232 Bytes
    #     # Directory count: 298
    #     # Other count....: 0
    #     # Hash over all files is: 452e0bfd5013d672121605e8fabb28c7db8e09fb2dd5bed12c5aa8d1932a12dd5f98d214c361e2e8d88ac0b95c24633d20b121a96c48c52c238377b7269bd97c
    #     #  *** Duration: 11.62sec.
    #
    #     skip_dirs=('.config', '.local'),
    #     skip_filenames=('meld', 'aw-qt'),
    # )
    # walker.scandir()
    # walker.print_stats()

    walker = TwoSteps2(
        # top_path='~/bin',
        top_path='~/Sync',
        # File count.....: 7776 with 7502514116 Bytes
        # Directory count: 298
        # Other count....: 0
        # Hash over all files is: 452e0bfd5013d672121605e8fabb28c7db8e09fb2dd5bed12c5aa8d1932a12dd5f98d214c361e2e8d88ac0b95c24633d20b121a96c48c52c238377b7269bd97c
        #  *** Duration: 11.61sec.

        skip_dirs=('.config', '.local'),
        skip_filenames=('meld', 'aw-qt'),
    )
    walker.scandir()
    walker.print_stats()

    duration = time.time() - start_time
    print(f' *** Duration: {duration:.2f}sec.')

    # with threads: ~/bin 3946 items -> 11,8sec
