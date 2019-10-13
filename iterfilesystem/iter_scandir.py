import fnmatch
import logging
import os
from pathlib import Path

log = logging.getLogger()


class ScandirWalker:
    def __init__(
            self,
            *,
            top_path,
            stats_helper,
            skip_dir_patterns=(),
            skip_file_patterns=(),
            verbose=True):
        self.verbose = verbose
        self.top_path = self.get_top_path(top_path)
        self.stats_helper = stats_helper
        self.skip_dir_patterns = self.get_skip_dir_patterns(skip_dir_patterns)
        self.skip_file_patterns = self.get_skip_file_patterns(skip_file_patterns)

    ##############################################################################################
    # These methods may be overwritten:

    def get_top_path(self, top_path):
        if self.verbose:
            print(f'Read/process: {top_path!r}...')
        top_path = Path(top_path).expanduser().resolve()
        if not top_path.is_dir():
            raise NotADirectoryError(f'Directory does not exists: {top_path}')
        return top_path

    def get_pattern(self, kind, skip_patterns):
        if self.verbose:
            if skip_patterns:
                print(f'Skip {kind} patterns:')
                print('\t* ' + '\n\t* '.join(skip_patterns))
                print()
            else:
                print(f'No skip {kind} patterns, ok.')
        return skip_patterns

    def get_skip_dir_patterns(self, skip_dir_patterns):
        return self.get_pattern(kind='directory', skip_patterns=skip_dir_patterns)

    def get_skip_file_patterns(self, skip_file_patterns):
        return self.get_pattern(kind='file', skip_patterns=skip_file_patterns)

    def on_skip_dir(self, dir_entry):
        pass

    def on_skip_file(self, dir_entry):
        pass

    ##############################################################################################

    def fnmatches(self, dir_item_name, patterns):
        for skip_pattern in patterns:
            if fnmatch.fnmatch(dir_item_name, skip_pattern):
                return True
        return False

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
                if self.fnmatches(dir_item_name=dir_entry.name, patterns=self.skip_dir_patterns):
                    self.stats_helper.walker_dir_skip_count += 1
                    self.on_skip_dir(dir_entry)
                else:
                    self.stats_helper.walker_dir_count += 1
                    yield dir_entry
                    yield from self._iter_scandir(dir_entry.path)
            else:
                if self.fnmatches(dir_item_name=dir_entry.name, patterns=self.skip_file_patterns):
                    self.stats_helper.walker_file_skip_count += 1
                    self.on_skip_file(dir_entry)
                else:
                    self.stats_helper.walker_file_count += 1
                    yield dir_entry
