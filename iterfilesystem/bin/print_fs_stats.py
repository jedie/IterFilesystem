#!/usr/bin/env python3


'''
This sample script will get deployed in the bin directory of the
users' virtualenv when the parent module is installed using pip.
'''

import argparse
import logging
import sys
import traceback
from pathlib import Path

from iterfilesystem import get_module_version
from iterfilesystem.example import CountFilesystemWalker
from iterfilesystem.iter_scandir import ScandirWalker

log = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s')


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
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        '--path',
        help='The file path that should be scanned e.g.: "~/foobar/" default is "~"',
        default=Path('~')
    )
    parser.add_argument(
        '--skip_dirs',
        default=(),
        nargs='*',
        help='Directory names to exclude from scan.'
    )
    parser.add_argument(
        '--skip_filenames',
        default=(),
        nargs='*',
        help='File names to ignore.'
    )
    parser.add_argument(
        '--force_restart',
        action='store_true',
        help="Don't use resume data: Delete persist queue data before start."
    )
    parser.add_argument(
        '--complete_cleanup',
        action='store_true',
        help="Delete persist queue after complete scan."
    )

    if args:
        print(f'Use args: {args!r}')
    else:
        args = None

    args = parser.parse_args(args)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    try:
        scandir_walker = ScandirWalker(
            top_path=args.path,
            skip_dirs=args.skip_dirs,
            skip_filenames=args.skip_filenames,
        )
        walker = CountFilesystemWalker(
            scandir_walker=scandir_walker,
            force_restart=args.force_restart,
            complete_cleanup=args.complete_cleanup,
        )

        try:
            walker.scandir()
        except KeyboardInterrupt:
            pass  # print stats after Strg-C

        walker.print_stats()

        # # Do your work here - preferably in a class or function,
        # # passing in your args. E.g.
        # exe = Example(args.first)
        # exe.update_value(args.second)
        # print('First : {}\nSecond: {}'.format(exe.get_value(), exe.get_previous_value()))

    except Exception as e:
        log.error('=============================================')
        if args.debug:
            log.error('\n\n' + traceback.format_exc())
            log.error('=============================================')
        log.error('\n\n' + str(e) + '\n')
        log.error('=============================================')
        sys.exit(1)


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)

if __name__ == '__main__':
    main()
