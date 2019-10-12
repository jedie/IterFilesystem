from pathlib import Path

# IterFilesystem
import iterfilesystem


class BaseTestCase:
    package_path = Path(iterfilesystem.__file__).parent.parent

    skip_dirs = [x.name for x in package_path.iterdir() if x.is_dir() and x.name.startswith('.')]
    skip_dirs += ['build', 'dist', 'htmlcov', 'iterfilesystem.egg-info']

    skip_filenames = [
        x.name for x in package_path.iterdir() if x.is_file() and x.name.startswith('.')
    ]
