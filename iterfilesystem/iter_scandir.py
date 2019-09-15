import logging
import os
from pathlib import Path

log = logging.getLogger()


class ScandirWalker:
    def __init__(self, *, top_path, skip_dirs=(), skip_filenames=()):
        self.top_path = self.get_top_path(top_path)
        self.skip_dirs = self.get_skip_dirs(skip_dirs)
        self.skip_filenames = self.get_skip_filenames(skip_filenames)

    ##############################################################################################
    # These methods should be overwritten:

    def get_top_path(self, top_path):
        print(f'Read/process: {top_path!r}...')
        top_path = Path(top_path).expanduser().resolve()
        return top_path

    def get_skip_dirs(self, skip_dirs):
        if skip_dirs:
            print('Skip directories:')
            print('\t* ' + '\n\t* '.join(skip_dirs))
            print()
        return skip_dirs

    def get_skip_filenames(self, skip_filenames):
        if skip_filenames:
            print('Skip files:')
            print('\t* ' + '\n\t* '.join(skip_filenames))
            print()
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
            if dir_entry.is_dir(follow_symlinks=False):
                if dir_entry.name in self.skip_dirs:
                    self.on_skip_dir(dir_entry)
                else:
                    yield dir_entry
                    yield from self._iter_scandir(dir_entry.path)
            else:
                if dir_entry.name in self.skip_filenames:
                    self.on_skip_file(dir_entry)
                else:
                    yield dir_entry
