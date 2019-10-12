import sys
from pathlib import Path
from textwrap import shorten

# https://github.com/tqdm/tqdm
from tqdm import tqdm


class Printer:
    @classmethod
    def write(cls, *args, **kwargs):
        tqdm.write('\r\n')
        tqdm.write(*args, **kwargs)
        tqdm.write('\n')


class DirEntryTqdm(tqdm):
    def __init__(self, position=0):
        super().__init__(
            desc='Filesystem items..',
            position=position,
            unit="entries",
            total=sys.maxsize,
            bar_format='{l_bar}{bar}|{n_fmt}/{total_fmt} {rate_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
            dynamic_ncols=True,
        )

    def update(self, statistics, dir_entry):
        self.total = max(statistics.total_dir_item_count, statistics.dir_item_count)
        self.n = statistics.dir_item_count
        self.refresh(nolock=True)


class FileSizeTqdm(tqdm):
    def __init__(self, position=0):
        super().__init__(
            desc='File sizes........',
            position=position,
            unit_scale=True,
            unit_divisor=1024,
            unit="Bytes",
            total=sys.maxsize,
            bar_format='{l_bar}{bar}|{n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
            dynamic_ncols=True,
        )

    def update(self, statistics, dir_entry):
        self.total = max(statistics.total_file_size, statistics.total_file_size_processed)
        self.n = statistics.total_file_size_processed
        self.refresh(nolock=True)


class WorkerTqdm(tqdm):
    def __init__(self, position=0):
        super().__init__(
            desc='Average progress..',
            position=position,
            total=100,
            bar_format='{l_bar}{bar}|{elapsed}<{remaining} {postfix}',
            dynamic_ncols=True,
        )

    def update(self, statistics, dir_entry):
        def percent(current, total):
            if total == 0:
                return 0
            return current / total * 100

        count_percent = percent(statistics.dir_item_count, statistics.total_dir_item_count)
        size_percent = percent(statistics.total_file_size_processed, statistics.total_file_size)

        avg_percent = (count_percent + size_percent) / 2

        self.n = avg_percent
        self.refresh(nolock=True)


class PostfixOnlyTqdm(tqdm):
    def __init__(self, desc, position=0, leave=True):
        super().__init__(
            desc=desc,
            position=position,
            total=sys.maxsize,
            bar_format='{desc}:{postfix}',
            dynamic_ncols=True,
            leave=leave,
        )


class FileNameTqdm(PostfixOnlyTqdm):
    def __init__(self, position=0):
        super().__init__(
            desc='Current File......',
            position=position,
        )
        if not self.ncols:
            self.path_width = 50
        else:
            self.path_width = self.ncols - 10

    def update(self, statistics, dir_entry):
        self.postfix = shorten(
            str(Path(dir_entry).resolve()),
            width=self.path_width,
            placeholder='...'
        )
        self.total = statistics.total_dir_item_count
        self.n = statistics.dir_item_count
        self.refresh(nolock=True)


class FileProcessingTqdm(tqdm):
    def __init__(self):
        super().__init__(
            desc="",
            position=4,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            total=sys.maxsize,
            dynamic_ncols=True,
            leave=True,
        )


class FilesystemWorkerProcessBar:
    def __init__(self):
        tqdm.monitor_interval = 0

    def __enter__(self):
        self.bars = (
            DirEntryTqdm(position=0),
            FileSizeTqdm(position=1),
            WorkerTqdm(position=2),
            FileNameTqdm(position=3),
        )
        return self

    def update(self, statistics, dir_entry):
        for bar in self.bars:
            bar.update(statistics, dir_entry)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for bar in self.bars:
            bar.close()

        print('\n')
