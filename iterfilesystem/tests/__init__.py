from pathlib import Path

import iterfilesystem


class BaseTestCase:
    package_path = Path(iterfilesystem.__file__).parent.parent
    skip_dirs = [x.name for x in package_path.iterdir() if x.is_dir() and x.name.startswith('.')]
    skip_filenames = [x.name for x in package_path.iterdir() if x.is_file() and x.name.startswith('.')]
