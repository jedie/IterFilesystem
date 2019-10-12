from pathlib import Path

# IterFilesystem
import iterfilesystem


class BaseTestCase:
    package_path = Path(iterfilesystem.__file__).parent.parent

    skip_dir_patterns = (
        '.*', 'build', 'dist', 'htmlcov', '*.egg-info'
    )
    skip_file_patterns = (
        '.*', '*.egg-info'
    )
