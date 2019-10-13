#!/usr/bin/env python3

import hashlib
from pathlib import Path

# IterFilesystem
from iterfilesystem.humanize import human_filesize
from iterfilesystem.iter_scandir import ScandirWalker
from iterfilesystem.main import IterFilesystem


class CalcFilesystemSHA512(IterFilesystem):
    def start(self):
        self.hash = hashlib.sha512()
        super().start()

    def process_dir_entry(self, dir_entry, process_bars):
        if not dir_entry.is_file(follow_symlinks=False):
            # Skip all non files
            return

        collect_file_size = dir_entry.stat().st_size
        big_file = collect_file_size > 10 * 1024 * 1024

        if big_file:
            process_bars.file_bar.desc = f'Calc SHA512 for "{dir_entry.name}"'
            process_bars.file_bar.reset(total=dir_entry.stat().st_size)

        with Path(dir_entry).open('rb') as f:
            process_size = 0
            while True:
                data = f.read(100000)
                if not data:
                    break
                self.hash.update(data)

                process_size += len(data)

                if big_file and self.update_file_interval:
                    process_bars.file_bar.update(process_size)
                    self.update(
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
                file_size=collect_file_size,
                process_bars=process_bars
            )

    def done(self):
        self.stats_helper.hash = self.hash.hexdigest()  # Just add hash to statistics ;)


def calc_sha512(*, top_path, skip_dir_patterns=(), skip_file_patterns=(), wait=False):
    calc_sha = CalcFilesystemSHA512(
        ScanDirClass=ScandirWalker,
        scan_dir_kwargs=dict(
            top_path=top_path,
            skip_dir_patterns=skip_dir_patterns,
            skip_file_patterns=skip_file_patterns,
        ),
        update_interval_sec=0.5,
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
        # top_path='~',
        # top_path='~/bin',
        top_path='~/repos',
        skip_dir_patterns=('.tox', '.config', '.local', 'temp', '__cache__'),
        skip_file_patterns=('*.temp', '*.egg-info'),
    )

    print(stats_helper.pformat())

    # calc_sha512(path='~/Downloads')
