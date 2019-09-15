#!/usr/bin/env python3
import logging
from pathlib import Path

# https://github.com/peter-wangxu/persist-queue
from persistqueue.sqlackqueue import AckStatus

# IterFilesystem
from iterfilesystem import ThreadedFilesystemWalker
from iterfilesystem.iter_scandir import ScandirWalker


class FilesystemInformation:
    file_count = 0
    file_size = 0
    dir_count = 0
    other_count = 0


class CountFilesystemWalker(ThreadedFilesystemWalker):
    def __init__(self, *args, **kwargs):
        self.fs_info = FilesystemInformation()
        super().__init__(*args, **kwargs)

    def process_path_item(self, path):
        fs_item = Path(path)

        with self.lock:
            if fs_item.is_dir():
                self.fs_info.dir_count += 1
            elif fs_item.is_file():
                self.fs_info.file_size += fs_item.stat().st_size
                self.fs_info.file_count += 1
            else:
                self.fs_info.other_count += 1

        # time.sleep(random.random() * 0.001)  # 'simulating' more process time

        return AckStatus.acked

    def print_stats(self):
        print(f'File count.....: {self.fs_info.file_count} with {self.fs_info.file_size} Bytes')
        print(f'Directory count: {self.fs_info.dir_count}')
        print(f'Other count....: {self.fs_info.other_count}')

        seen_count = self.fs_info.file_count + self.fs_info.dir_count + self.fs_info.other_count
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


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO
        # level=logging.DEBUG
    )

    walker = count_filesystem(
        top_path='~/bin',

        skip_dirs=('.config', '.local'),
        skip_filenames=('meld', 'aw-qt'),

        # force_restart=True,
        force_restart=False,

        complete_cleanup=True,

        worker_count=3,

        update_interval_sec=0.5
    )
    walker.print_stats()
