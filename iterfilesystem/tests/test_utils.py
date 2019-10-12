import tempfile
from pathlib import Path

# IterFilesystem
from iterfilesystem.utils import get_persist_temp_path


def test_get_persist_temp_path():
    persist_path = get_persist_temp_path(seed='1')
    assert persist_path == Path(tempfile.gettempdir(), 'iterfilesystem_Tf9Oo')

    persist_path = get_persist_temp_path(seed='2')
    assert persist_path == Path(tempfile.gettempdir(), 'iterfilesystem_QLJEE')


def verbose_get_capsys(capsys):
    captured = capsys.readouterr()

    captured_out = captured.out
    print('_' * 100)
    print('Captured stdout:')
    print(captured_out)
    print('-' * 100)

    captured_err = captured.err
    print('_' * 100)
    print('Captured stderr:')
    print(captured_err)
    print('-' * 100)
    return captured_out, captured_err
