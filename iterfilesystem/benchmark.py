# IterFilesystem
from iterfilesystem.iter_scandir import ScandirWalker
from iterfilesystem.statistics import Statistics
from iterfilesystem.utils import UpdateInterval


def main(top_path):
    statistics = Statistics()

    sw = ScandirWalker(
        top_path=top_path,
        statistics=statistics,
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

    statistics.print_stats()


if __name__ == '__main__':
    main(top_path='~/hoods')
