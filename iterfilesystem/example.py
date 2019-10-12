#!/usr/bin/env python3

import hashlib
from pathlib import Path
from timeit import default_timer

# IterFilesystem
from iterfilesystem.humanize import human_filesize
from iterfilesystem.iter_scandir import ScandirWalker
from iterfilesystem.main import FilesystemBaseWorker, FilesystemWorker
from iterfilesystem.process_bar import FileProcessingTqdm
from iterfilesystem.utils import UpdateInterval


class CalcSHA512Worker(FilesystemBaseWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hash = hashlib.sha512()
        self.process_bar = FileProcessingTqdm()
        self.update_interval = UpdateInterval(interval=self.update_interval_sec)

    def process(self, *, dir_entry):
        if not dir_entry.is_file(follow_symlinks=False):
            # Skip all non files
            return

        total_file_size = dir_entry.stat().st_size
        big_file = total_file_size > 10 * 1024 * 1024

        if big_file:
            self.process_bar.desc = f'Calc SHA512 for "{dir_entry.name}"'
            self.process_bar.reset(total=dir_entry.stat().st_size)

        with Path(dir_entry).open('rb') as f:
            processed_size = 0
            while True:
                data = f.read(100000)
                if not data:
                    break
                self.hash.update(data)

                processed_size += len(data)

                if big_file and self.update_interval:
                    self.process_bar.update(processed_size)
                    self.update(dir_entry=dir_entry, file_size=processed_size)
                    processed_size = 0

        if big_file:
            self.process_bar.update(processed_size)
            self.update(dir_entry=dir_entry, file_size=processed_size)
        else:
            # Always update the global statistics / process bars:
            self.update(dir_entry=dir_entry, file_size=total_file_size)

    def done(self):
        self.process_bar.close()

        self.statistics.hash = self.hash.hexdigest()  # Just add hash to statistics ;)

        return super().done()  # return the statistics


def calc_sha512(*, top_path, skip_dir_patterns=(), skip_file_patterns=(), wait=False):
    fs_worker = FilesystemWorker(
        ScanDirClass=ScandirWalker,
        scan_dir_kwargs=dict(
            top_path=top_path,
            skip_dir_patterns=skip_dir_patterns,
            skip_file_patterns=skip_file_patterns,
        ),
        WorkerClass=CalcSHA512Worker,
        update_interval_sec=0.5,
        wait=wait
    )

    start_time = default_timer()
    statistics = fs_worker.process()
    duration = default_timer() - start_time

    print('\n\n')
    print(f'Processed {statistics.total_dir_item_count} filesystem items in {duration:.2f} sec')
    print(f'SHA515 hash calculated over all file content: {statistics.hash}')
    print(f'File count: {statistics.file_count}')
    print(f'Total file size: {human_filesize(statistics.total_file_size)}')

    if skip_dir_patterns:
        print(f'{statistics.skip_dir_count} directories skipped.')

    if skip_file_patterns:
        print(f'{statistics.skip_file_count} files skipped.')

    return statistics


if __name__ == '__main__':
    statistics = calc_sha512(
        # top_path='/foo/bar/',
        top_path='~',
        # top_path='~/bin',
        skip_dir_patterns=('.config', '.local', 'temp', '__cache__'),
        skip_file_patterns=('*.temp', '*.egg-info'),
    )

    print(statistics.pformat())

    # calc_sha512(path='~/Downloads')
