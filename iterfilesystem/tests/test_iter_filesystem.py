import logging
import time
from pathlib import Path

# IterFilesystem
from iterfilesystem.iter_scandir import ScandirWalker
from iterfilesystem.main import IterFilesystem


def test_iter_filesystem_collect_counts(tmp_path, capsys, caplog):
    for no in range(10):
        Path(tmp_path, f'file_{no}.txt').touch()

    with caplog.at_level(logging.DEBUG, logger="iterfilesystem"):
        iter_fs = IterFilesystem(
            ScanDirClass=ScandirWalker,
            scan_dir_kwargs=dict(
                top_path=tmp_path,
                skip_dir_patterns=(),
                skip_file_patterns=(),
            ),
            update_interval_sec=0.1,
            wait=True,
        )

        counts_dict = {}
        iter_fs._collect_counts(counts_dict)

    captured = capsys.readouterr()

    stdout = captured.out
    print('_' * 100)
    print('stdout:')
    print(stdout)
    print('=' * 100)

    assert captured.err == ''

    assert 'No skip directory patterns, ok.' in stdout
    assert 'No skip file patterns, ok.' in stdout
    assert 'Collect filesystem item process done' in stdout
    assert '(10 items)' in stdout

    assert set(counts_dict.keys()) == {'count duration', 'count done', 'dir item count'}
    assert counts_dict['count done'] is True
    assert counts_dict['dir item count'] == 10


def test_iter_filesystem_collect_size(tmp_path, capsys, caplog):
    for no in range(10):
        with Path(tmp_path, f'file_{no}.txt').open('wb') as f:
            f.write(b'XX')

    with caplog.at_level(logging.DEBUG, logger="iterfilesystem"):
        iter_fs = IterFilesystem(
            ScanDirClass=ScandirWalker,
            scan_dir_kwargs=dict(
                top_path=tmp_path,
                skip_dir_patterns=(),
                skip_file_patterns=(),
            ),
            update_interval_sec=0.1,
            wait=True,
        )
        size_dict = {}
        iter_fs._collect_size(size_dict)

    captured = capsys.readouterr()

    stdout = captured.out
    print('_' * 100)
    print('stdout:')
    print(stdout)
    print('=' * 100)

    print('_' * 100)
    print('stderr:')
    print(captured.err)
    print('=' * 100)

    assert captured.err == ''

    assert 'No skip directory patterns, ok.' in stdout
    assert 'No skip file patterns, ok.' in stdout
    assert 'Collect file size process done' in stdout
    assert '(20 Bytes)' in stdout

    assert set(size_dict.keys()) == {'size duration', 'file size', 'size done'}
    assert size_dict['size done'] is True
    assert size_dict['file size'] == 20


def test_iter_filesystem(tmp_path, capsys, caplog):
    for no in range(10):
        with Path(tmp_path, f'file_{no}.txt').open('wb') as f:
            f.write(b'XX')

    with caplog.at_level(logging.DEBUG, logger="iterfilesystem"):
        class TestIterFilesystem(IterFilesystem):
            def process_dir_entry(self, dir_entry, process_bars):
                print(dir_entry.name)
                time.sleep(0.01)
                self.update(
                    dir_entry=dir_entry,
                    file_size=dir_entry.stat().st_size,
                    process_bars=process_bars
                )

        iter_fs = TestIterFilesystem(
            ScanDirClass=ScandirWalker,
            scan_dir_kwargs=dict(
                top_path=tmp_path,
                skip_dir_patterns=(),
                skip_file_patterns=(),
            ),
            update_interval_sec=0.01,
            wait=True,
        )
        stats_helper = iter_fs.process()

    assert stats_helper.abort is False

    stats_helper.print_stats()

    assert stats_helper.walker_dir_count == 0
    assert stats_helper.walker_file_count == 10
    assert stats_helper.walker_dir_skip_count == 0
    assert stats_helper.walker_file_skip_count == 0

    logs = caplog.text
    print('-' * 100)
    print(logs)
    print('-' * 100)

    assert 'DEBUG Read/process:' in logs
    assert 'WARNING Wait set!' in logs
    assert 'INFO Worker starts' in logs
    assert 'INFO Worker done.' in logs

    assert 'INFO Set lower ionice priority' in logs
    assert 'INFO Set lower nice priority' in logs
    assert 'INFO Set higher ionice priority' in logs


def test_keyboard_interrupt(tmp_path, capsys):
    for no in range(5):
        Path(tmp_path, f'file_{no}.txt').touch()

    class TestIterFilesystem(IterFilesystem):
        def process_dir_entry(self, dir_entry, process_bars):
            print(dir_entry.name)
            if dir_entry.name == 'file_2.txt':
                raise KeyboardInterrupt
            self.update(
                dir_entry=dir_entry,
                file_size=dir_entry.stat().st_size,
                process_bars=process_bars
            )

    backup_worker = TestIterFilesystem(
        ScanDirClass=ScandirWalker,
        scan_dir_kwargs=dict(
            top_path=tmp_path,
            skip_dir_patterns=(),
            skip_file_patterns=(),
        ),
        update_interval_sec=0.5,
    )
    stats_helper = backup_worker.process()

    stats_helper.print_stats()

    assert stats_helper.abort is True  # KeyboardInterrupt was raised

    captured = capsys.readouterr()

    stdout = captured.out
    print('_' * 100)
    print('stdout:')
    print(stdout)
    print('=' * 100)

    stderr = captured.err
    print('_' * 100)
    print('stderr:')
    print(stderr)
    print('=' * 100)

    assert '*** Abort via keyboard interrupt! ***' in stderr
    assert 'file_0.txt\nfile_1.txt\nfile_2.txt\n' in stdout

    assert stats_helper.walker_dir_count == 0
    assert stats_helper.walker_file_count == 3
    assert stats_helper.walker_dir_skip_count == 0
    assert stats_helper.walker_file_skip_count == 0
