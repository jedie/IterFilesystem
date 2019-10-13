#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys

from setuptools import find_packages, setup

# IterFilesystem
from iterfilesystem import __version__

PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))


# _____________________________________________________________________________
# convert creole to ReSt on-the-fly, see also:
# https://github.com/jedie/python-creole/wiki/Use-In-Setup
long_description = None
for arg in ("test", "check", "register", "sdist", "--long-description"):
    if arg in sys.argv:
        try:
            from creole.setup_utils import get_long_description
        except ImportError as err:
            raise ImportError(
                "%s - Please install python-creole - e.g.: pip install python-creole" %
                err)
        else:
            long_description = get_long_description(PACKAGE_ROOT)
        break
# ----------------------------------------------------------------------------

if "publish" in sys.argv:
    """
    'publish' helper for setup.py

    Build and upload to PyPi, if...
        ... __version__ doesn't contains "dev"
        ... we are on git 'master' branch
        ... git repository is 'clean' (no changed files)

    Upload with "twine", git tag the current version and git push --tag

    The cli arguments will be pass to 'twine'. So this is possible:
     * Display 'twine' help page...: ./setup.py publish --help
     * use testpypi................: ./setup.py publish --repository=test

    TODO: Look at: https://github.com/zestsoftware/zest.releaser

    Source: https://github.com/jedie/python-code-snippets/blob/master/CodeSnippets/setup_publish.py
    copyleft 2015-2019 Jens Diemer - GNU GPL v2+
    """
    assert sys.version_info[0] > 2, "Python v3 is needed!"

    import_error = False
    try:
        # Test if wheel is installed, otherwise the user will only see:
        #   error: invalid command 'bdist_wheel'
        import wheel  # noqa
    except ImportError as err:
        print("\nError: %s\n" % err)
        print(
            "Maybe https://pypi.org/project/wheel is not installed"
            " or virtualenv not activated?!?"
        )
        print("e.g.:")
        print("    ~/your/env/$ source bin/activate")
        print("    ~/your/env/$ pip install wheel")
        import_error = True

    try:
        import twine  # noqa
    except ImportError as err:
        print("\nError: %s\n" % err)
        print(
            "Maybe https://pypi.org/project/twine is not installed"
            " or virtualenv not activated?!?"
        )
        print("e.g.:")
        print("    ~/your/env/$ source bin/activate")
        print("    ~/your/env/$ pip install twine")
        import_error = True

    if import_error:
        sys.exit(-1)

    def verbose_check_output(*args):
        """ 'verbose' version of subprocess.check_output() """
        call_info = "Call: %r" % " ".join(args)
        try:
            output = subprocess.check_output(
                args, universal_newlines=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            print("\n***ERROR:")
            print(err.output)
            raise
        return call_info, output

    def verbose_check_call(*args):
        """ 'verbose' version of subprocess.check_call() """
        print("\tCall: %r\n" % " ".join(args))
        subprocess.check_call(args, universal_newlines=True)

    def confirm(txt):
        print("\n%s" % txt)
        if input("\nPublish anyhow? (Y/N)").lower() not in ("y", "j"):
            print("Bye.")
            sys.exit(-1)

    for key in ("dev", "rc"):
        if key in __version__:
            confirm("WARNING: Version contains %r: v%s\n" % (key, __version__))
            break

    print("\nCheck if we are on 'master' branch:")
    call_info, output = verbose_check_output("git", "branch", "--no-color")
    print("\t%s" % call_info)
    if "* master" in output:
        print("OK")
    else:
        confirm("\nNOTE: It seems you are not on 'master':\n%s" % output)

    print("\ncheck if if git repro is clean:")
    call_info, output = verbose_check_output("git", "status", "--porcelain")
    print("\t%s" % call_info)
    if output == "":
        print("OK")
    else:
        print("\n *** ERROR: git repro not clean:")
        print(output)
        sys.exit(-1)

    print("\nRun './setup.py check':")
    call_info, output = verbose_check_output("./setup.py", "check")
    if "warning" in output:
        print(output)
        confirm("Warning found!")
    else:
        print("OK")

    print("\ncheck if pull is needed")
    verbose_check_call("git", "fetch", "--all")
    call_info, output = verbose_check_output("git", "log", "HEAD..origin/master", "--oneline")
    print("\t%s" % call_info)
    if output == "":
        print("OK")
    else:
        print("\n *** ERROR: git repro is not up-to-date:")
        print(output)
        sys.exit(-1)
    verbose_check_call("git", "push")

    print("\nCleanup old builds:")

    def rmtree(path):
        path = os.path.abspath(path)
        if os.path.isdir(path):
            print("\tremove tree:", path)
            shutil.rmtree(path)
    rmtree("./dist")
    rmtree("./build")

    print("\nbuild but don't upload...")
    log_filename = "build.log"
    with open(log_filename, "a") as log:
        call_info, output = verbose_check_output(
            sys.executable or "python",
            "setup.py", "sdist", "bdist_wheel", "bdist_egg"
        )
        print("\t%s" % call_info)
        log.write(call_info)
        log.write(output)
    print("Build output is in log file: %r" % log_filename)

    git_tag = "v%s" % __version__

    print("\ncheck git tag")
    call_info, output = verbose_check_output("git", "log", "HEAD..origin/master", "--oneline")
    if git_tag in output:
        print("\n *** ERROR: git tag %r already exists!" % git_tag)
        print(output)
        sys.exit(-1)
    else:
        print("OK")

    print("\nUpload with twine:")
    twine_args = sys.argv[1:]
    twine_args.remove("publish")
    twine_args.insert(1, "dist/*")
    print("\ttwine upload command args: %r" % " ".join(twine_args))
    from twine.commands.upload import main as twine_upload
    twine_upload(twine_args)

    print("\ngit tag version")
    verbose_check_call("git", "tag", git_tag)

    print("\ngit push tag to server")
    verbose_check_call("git", "push", "--tags")

    sys.exit(0)


setup(
    author="Jens Diemer",
    author_email='python@jensdiemer.de',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description=(
        "Multiprocess directory iteration via os.scandir()"
        " with progress indicator via tqdm bars."
    ),
    install_requires=[
        'tqdm',
        'psutil',
    ],
    entry_points={
        'console_scripts': [
            'print_fs_stats=iterfilesystem.bin.print_fs_stats:main'
        ],
    },
    license="GNU General Public License v3",
    long_description=long_description,
    include_package_data=True,
    keywords='iterfilesystem',
    name='iterfilesystem',
    packages=find_packages(),
    python_requires=">=3.6",
    test_suite='iterfilesystem/tests',
    url='https://github.com/jedie/iterfilesystem',
    version=__version__,
    zip_safe=False,
)
