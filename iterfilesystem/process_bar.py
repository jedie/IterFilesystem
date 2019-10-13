import sys
from pathlib import Path
from statistics import median_low
from textwrap import shorten

# https://github.com/tqdm/tqdm
from tqdm import tqdm


class Printer:
    @classmethod
    def write(cls, s, file=None, end='\n', nolock=False):
        tqdm.write('\r\n\n\n\n')
        if '\n' in end:
            s = s.rstrip()
        tqdm.write(s, file=file, end=end, nolock=nolock)


class DirEntryTqdm(tqdm):
    def __init__(self, position=None):
        super().__init__(
            desc='Filesystem items..',
            position=position,
            unit="entries",
            total=sys.maxsize,
            bar_format=(
                '{l_bar}{bar}|{n_fmt}/{total_fmt} {rate_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            ),
            dynamic_ncols=True,
        )

    def update(self, stats_helper, dir_entry):
        walker_dir_item_count = stats_helper.get_walker_dir_item_count()
        self.total = max(stats_helper.collect_dir_item_count, walker_dir_item_count)
        self.n = walker_dir_item_count
        self.refresh(nolock=True)


class FileSizeTqdm(tqdm):
    def __init__(self, position=None):
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

    def update(self, stats_helper, dir_entry):
        self.total = max(stats_helper.collect_file_size, stats_helper.process_file_size)
        self.n = stats_helper.process_file_size
        self.refresh(nolock=True)


class WorkerTqdm(tqdm):
    def __init__(self, position=None):
        super().__init__(
            desc='Average progress..',
            position=position,
            total=100,
            bar_format='{l_bar}{bar}|{elapsed}<{remaining} {postfix}',
            dynamic_ncols=True,
        )

    def update(self, stats_helper, dir_entry):
        def percent(current, total):
            if total == 0:
                return 0
            return current / total * 100

        count_percent = percent(
            current=stats_helper.get_walker_dir_item_count(),
            total=stats_helper.collect_dir_item_count
        )
        size_percent = percent(
            current=stats_helper.process_file_size,
            total=stats_helper.collect_file_size
        )

        self.n = median_low([count_percent, size_percent])
        self.refresh(nolock=True)


class PostfixOnlyTqdm(tqdm):
    def __init__(self, desc, position=None, leave=True):
        super().__init__(
            desc=desc,
            position=position,
            total=sys.maxsize,
            bar_format='{desc}:{postfix}',
            dynamic_ncols=True,
            leave=leave,
        )


class FileNameTqdm(PostfixOnlyTqdm):
    def __init__(self, position=None):
        super().__init__(
            desc='Current File......',
            position=position,
        )
        if not self.ncols:
            self.path_width = 50
        else:
            self.path_width = self.ncols - 10

    def update(self, stats_helper, dir_entry):
        self.postfix = shorten(
            str(Path(dir_entry).resolve()),
            width=self.path_width,
            placeholder='...'
        )
        self.total = stats_helper.collect_dir_item_count
        self.n = stats_helper.get_walker_dir_item_count()
        self.refresh(nolock=True)


class FileProcessingTqdm(tqdm):
    def __init__(self, position=None):
        super().__init__(
            desc="",
            position=position,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            total=sys.maxsize,
            dynamic_ncols=True,
            leave=True,
        )


class IterFilesystemProcessBar:
    def __init__(self):
        tqdm.monitor_interval = 0

    def __enter__(self):
        self.bars = (
            DirEntryTqdm(position=0),
            FileSizeTqdm(position=1),
            WorkerTqdm(position=2),
            FileNameTqdm(position=3),
        )
        self.file_bar = FileProcessingTqdm(position=4)
        return self

    def update(self, stats_helper, dir_entry):
        for bar in self.bars:
            bar.update(stats_helper, dir_entry)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for bar in self.bars:
            bar.close()
        self.file_bar.close()

        print('\n')
