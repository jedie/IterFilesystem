#!/usr/bin/env python3

"""
    Example CLI program

    Will be "installed" by setup.py console_scripts / entry_points

    e.g.:

    (IterFilesystem) ~/IterFilesystem$ print_fs_stats --help
"""

import argparse
import logging
import sys
import traceback
from pathlib import Path

# IterFilesystem
import iterfilesystem
from iterfilesystem.example import calc_sha512

log = logging.getLogger(__name__)


def main(*args):
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description='Scan filesystem and print some information')
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s ' + iterfilesystem.__version__
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        dest='debug',
        help='enable DEBUG'
    )
    parser.add_argument(
        '--path',
        help='The file path that should be scanned e.g.: "~/foobar/" default is "~"',
        default=Path('~')
    )
    parser.add_argument(
        '--skip_dir_patterns',
        default=(),
        nargs='*',
        help='Directory names to exclude from scan.'
    )
    parser.add_argument(
        '--skip_file_patterns',
        default=(),
        nargs='*',
        help='File names to ignore.'
    )

    if args:
        print(f'Use args: {args!r}')
    else:
        args = None

    args = parser.parse_args(args)

    try:
        statistics = calc_sha512(
            top_path=args.path,
            skip_dir_patterns=args.skip_dir_patterns,
            skip_file_patterns=args.skip_file_patterns,
        )
    except NotADirectoryError as err:
        print(f'ERROR: {err}')
        sys.exit(1)
    except Exception:
        print('=' * 100, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        print('=' * 100, file=sys.stderr)
        sys.exit(-1)
    else:
        if args.debug:
            print('\ndebug statistics:')
            statistics.print_stats()
        print()


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)
if __name__ == '__main__':
    main()
