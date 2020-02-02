from pathlib import Path

# IterFilesystem
from iterfilesystem.iter_scandir import ScandirWalker
from iterfilesystem.main import IterFilesystem


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
            verbose=True
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
