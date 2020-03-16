#!/usr/bin/env python3

import hashlib
import sys
from pathlib import Path
from timeit import default_timer

# IterFilesystem
from iterfilesystem.humanize import human_filesize
from iterfilesystem.iter_scandir import ScandirWalker
from iterfilesystem.main import IterFilesystem


class CalcFilesystemSHA512(IterFilesystem):
    MIN_CHUNK_SIZE = 10 * 1024 * 1024
    MAX_CHUNK_SIZE = sys.maxsize

    def start(self):
        self.hash = hashlib.sha512()

        self.chunk_size = self.MIN_CHUNK_SIZE
        self.update_interval_trigger = self.update_interval_sec / 2

        self.big_file_count = 0
        super().start()

    def process_dir_entry(self, dir_entry, process_bars):
        if not dir_entry.is_file(follow_symlinks=False):
            # Skip all non files
            return

        file_size = dir_entry.stat().st_size
        small_file = file_size < self.chunk_size

        big_file = False
        with Path(dir_entry).open('rb') as f:
            process_size = 0
            while True:
                start_time = default_timer()
                try:
                    data = f.read(self.chunk_size)
                except MemoryError:
                    # Lower the chunk size to avoid memory errors
                    while self.chunk_size > 2:
                        self.chunk_size = int(self.chunk_size * 0.25)
                        self.MAX_CHUNK_SIZE = self.chunk_size
                        try:
                            data = f.read(self.chunk_size)
                        except MemoryError:
                            continue
                        else:
                            print(f'set max block size to: {self.MAX_CHUNK_SIZE} Bytes.')
                            break

                if not data:
                    break

                self.hash.update(data)
                chunk_size = len(data)
                process_size += chunk_size

                if not small_file and chunk_size == self.chunk_size:
                    # Display "current file processbar", but only for big files

                    # Calculate the chunk size, so we update the current file bar
                    # in self.update_interval_sec intervals
                    duration = default_timer() - start_time
                    if duration < self.update_interval_sec and self.chunk_size < self.MAX_CHUNK_SIZE:
                        self.chunk_size = min([int(self.chunk_size * 1.25), self.MAX_CHUNK_SIZE])
                    elif duration > self.update_interval_sec:
                        self.chunk_size = max([int(self.chunk_size * 0.75), self.MIN_CHUNK_SIZE])

                    if not big_file:
                        # init current file bar
                        process_bars.file_bar.reset(total=dir_entry.stat().st_size)
                        self.big_file_count += 1
                        big_file = True

                    # print the bar:
                    process_bars.file_bar.desc = (
                        f'{dir_entry.name}'
                        f' | {human_filesize(self.chunk_size)} chunks'
                        f' | {duration:.1f} sec.'
                    )
                    process_bars.file_bar.update(process_size)

                    self.update(  # Update statistics and global bars
                        dir_entry=dir_entry,
                        file_size=process_size,
                        process_bars=process_bars
                    )
                    process_size = 0

        if big_file:
            process_bars.file_bar.update(process_size)
            self.update(
                dir_entry=dir_entry,
                file_size=process_size,
                process_bars=process_bars
            )
        else:
            # Always update the global statistics / process bars:
            self.update(
                dir_entry=dir_entry,
                file_size=file_size,
                process_bars=process_bars
            )

    def done(self):
        self.stats_helper.hash = self.hash.hexdigest()  # Just add hash to statistics ;)
        print(f'There was {self.big_file_count} big files.')


def calc_sha512(*, top_path, skip_dir_patterns=(), skip_file_patterns=(), wait=False):
    calc_sha = CalcFilesystemSHA512(
        ScanDirClass=ScandirWalker,
        scan_dir_kwargs=dict(
            top_path=top_path,
            skip_dir_patterns=skip_dir_patterns,
            skip_file_patterns=skip_file_patterns,
        ),
        update_interval_sec=1,
        wait=wait
    )
    stats_helper = calc_sha.process()

    print('\n\n')
    print(
        f'Processed {stats_helper.collect_dir_item_count} filesystem items'
        f' in {stats_helper.process_duration:.2f} sec'
    )
    print(f'SHA515 hash calculated over all file content: {stats_helper.hash}')
    print(f'File count: {stats_helper.walker_file_count}')
    print(f'Total file size: {human_filesize(stats_helper.collect_file_size)}')

    if skip_dir_patterns:
        print(f'{stats_helper.walker_dir_skip_count} directories skipped.')

    if skip_file_patterns:
        print(f'{stats_helper.walker_file_skip_count} files skipped.')

    return stats_helper


if __name__ == '__main__':
    stats_helper = calc_sha512(
        # top_path='/foo/bar/',
        top_path=Path().cwd().parent,
        skip_dir_patterns=('.tox', '.config', '.local', 'temp', '__cache__'),
        skip_file_patterns=('*.temp', '*.egg-info'),
    )

    print(stats_helper.pformat())

    # calc_sha512(path='~/Downloads')
