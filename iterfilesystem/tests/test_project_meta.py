"""
    Some project meta tests
"""
import subprocess
import sys

import pytest
from flake8.main.cli import main


def test_flake8():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main([
            # "--verbose"
        ])

    assert pytest_wrapped_e.value.code == 0


def test_pipenv_check():
    # we can just call pipenv.core.do_check()
    # But this will fail on TravisCI and appveyor.com
    #
    # work-a-round:
    output = subprocess.check_output([sys.executable, "-m", "pipenv", "check"], universal_newlines=True, timeout=20)
    print(output)
    assert 'Passed!' in output
    assert 'All good!' in output
