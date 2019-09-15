from flake8.main.cli import main

import pytest


def test_flake8():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main([
            # "--verbose"
        ])

    assert pytest_wrapped_e.value.code == 0
