import tempfile
from pathlib import Path

# IterFilesystem
from iterfilesystem import get_persist_temp_path


def test_get_persist_temp_path():
    persist_path = get_persist_temp_path(seed='1')
    assert persist_path == Path(tempfile.gettempdir(), 'iterfilesystem_Tf9Oo')

    persist_path = get_persist_temp_path(seed='2')
    assert persist_path == Path(tempfile.gettempdir(), 'iterfilesystem_QLJEE')
