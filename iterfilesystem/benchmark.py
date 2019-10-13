# IterFilesystem
from iterfilesystem.iter_scandir import ScandirWalker
from iterfilesystem.statistic_helper import StatisticHelper
from iterfilesystem.utils import UpdateInterval


def main(top_path):
    stats_helper = StatisticHelper()

    sw = ScandirWalker(
        top_path=top_path,
        stats_helper=stats_helper,
        skip_dir_patterns=('.*', '*.egg-info'),
        skip_file_patterns=('.*', '*.temp', '*.bak'),
        verbose=True
    )

    update = UpdateInterval(interval=1)
    count = 0
    for _ in sw:
        count += 1
        if update:
            print(f'{count} dir items')

    stats_helper.print_stats()


if __name__ == '__main__':
    main(top_path='~/repos')
