import logging
import os
from pathlib import Path

log = logging.getLogger()


class ScandirWalker:
    def __init__(self, *, top_path, statistics, skip_dirs=(), skip_filenames=(), verbose=True):
        self.verbose = verbose
        self.top_path = self.get_top_path(top_path)
        self.statistics = statistics
        self.skip_dirs = self.get_skip_dirs(skip_dirs)
        self.skip_filenames = self.get_skip_filenames(skip_filenames)

    ##############################################################################################
    # These methods should be overwritten:

    def get_top_path(self, top_path):
        if self.verbose:
            print(f'Read/process: {top_path!r}...')
        top_path = Path(top_path).expanduser().resolve()
        if not top_path.is_dir():
            raise NotADirectoryError(f'Directory does not exists: {top_path}')
        return top_path

    def get_skip_dirs(self, skip_dirs):
        if self.verbose:
            if skip_dirs:
                print('Skip directories:')
                print('\t* ' + '\n\t* '.join(skip_dirs))
                print()
            else:
                print('No directories will be skipped.')
        return skip_dirs

    def get_skip_filenames(self, skip_filenames):
        if self.verbose:
            if skip_filenames:
                print('Skip files:')
                print('\t* ' + '\n\t* '.join(skip_filenames))
                print()
            else:
                print('No files will be skipped.')
        return skip_filenames

    def on_skip_dir(self, dir_entry):
        log.info('Skip dir: %r', dir_entry.name)

    def on_skip_file(self, dir_entry):
        log.info('Skip file: %r', dir_entry.name)

    ##############################################################################################

    def __iter__(self):
        yield from self._iter_scandir(path=self.top_path)

    def _iter_scandir(self, path):
        try:
            dir_entry_iterator = os.scandir(path)
        except PermissionError as err:
            log.error('scandir error: %s', err)
            return

        for dir_entry in dir_entry_iterator:
            self.statistics.dir_item_count += 1
            if dir_entry.is_dir(follow_symlinks=False):
                if dir_entry.name in self.skip_dirs:
                    self.statistics.skip_dir_count += 1
                    self.on_skip_dir(dir_entry)
                else:
                    self.statistics.dir_count += 1
                    yield dir_entry
                    yield from self._iter_scandir(dir_entry.path)
            else:
                if dir_entry.name in self.skip_filenames:
                    self.statistics.skip_file_count += 1
                    self.on_skip_file(dir_entry)
                else:
                    self.statistics.file_count += 1
                    yield dir_entry
