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
from iterfilesystem import get_module_version
from iterfilesystem.example import calc_sha512
from iterfilesystem.process_bar import Printer

log = logging.getLogger()


def main(*args):
    parser = argparse.ArgumentParser(prog=Path(__file__).name,
                                     description='Scan filesystem and print some information')
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s ' +
        get_module_version())

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

    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.ERROR

    logging.basicConfig(
        level=log_level,
        format='[%(processName)s %(levelname)4s:%(lineno)4s %(asctime)s] %(message)s',
        stream=Printer
    )

    try:
        statistics = calc_sha512(
            top_path=args.path,
            skip_dir_patterns=args.skip_dir_patterns,
            skip_file_patterns=args.skip_file_patterns,
        )
        if args.debug:
            print('\ndebug statistics:')
            statistics.print_stats()
        print()
    except NotADirectoryError as err:
        print(f'ERROR: {err}')
        sys.exit(1)
    except Exception as err:
        print('=' * 100, file=sys.stderr)
        if args.debug:
            print(traceback.format_exc(), file=sys.stderr)
            print('=' * 100, file=sys.stderr)
        print(err, file=sys.stderr)
        print('=' * 100, file=sys.stderr)
        sys.exit(-1)


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)
if __name__ == '__main__':
    main()
