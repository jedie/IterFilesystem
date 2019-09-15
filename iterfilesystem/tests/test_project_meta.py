"""
    Some project meta tests
"""

import pytest
from flake8.main.cli import main
from pipenv.core import do_check


def test_flake8():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main([
            # "--verbose"
        ])

    assert pytest_wrapped_e.value.code == 0


def test_pipenv_check(capsys):
    do_check()

    captured = capsys.readouterr()
    print(captured.out)
    assert 'Passed!' in captured.out
    assert 'All good!' in captured.out

    print(captured.err)
    assert captured.err == ""
