--------------
IterFilesystem
--------------

Multiprocess directory iteration via ``os.scandir()``

Who's this Lib for?

You want to process a large number of files and/or a few very big files and give feedback to the user on how long it will take.

Features:
=========

* Progress indicator:

    * Immediately after start: process files and indication of progress via multiprocess

    * process bars via `tqdm <https://pypi.org/project/tqdm/>`_

    * Estimated time based on file count and size

* Easy to implement extra process bar for big file processing.

* Skip directories and file name via fnmatch.

How it works:
=============

The main process starts *statistic* processes in background via Python multiprocess and starts directly with the work.

There are two background *statistic* processes collects information for the process bars:

* Count up all directories and files.

* Accumulates the sizes of all files.

Why two processes?

Because collect only the count of all filesystem items via ``os.scandir()`` is very fast. This is the fastest way to predict a processing time.

Use ``os.DirEntry.stat()`` to get the file size is significantly slower: It requires another system call.

OK, but why two processed?

Use only the total count of all ``DirEntry`` may result in bad estimated time Progress indication.
It depends on what the actual work is about: When processing the contents of large files, it is good to know how much total data to be processed.

That's why we used two ways: the ``DirEntry`` count to forecast a processing time very quickly and the size to improve the predicted time.

requirements:
=============

* Python 3.6 or newer.

* ``tqdm`` for process bars

* ``psutils`` for setting process priority

* For dev.: `Pipenv <https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv>`_. Packages and virtual environment manager

contribute
==========

Please: try, fork and contribute! ;)

+--------------------------------------+----------------------------------------------------------+
| |Build Status on travis-ci.org|      | `travis-ci.org/jedie/IterFilesystem`_                    |
+--------------------------------------+----------------------------------------------------------+
| |Build Status on appveyor.com|       | `ci.appveyor.com/project/jedie/IterFilesystem`_          |
+--------------------------------------+----------------------------------------------------------+
| |Coverage Status on codecov.io|      | `codecov.io/gh/jedie/IterFilesystem`_                    |
+--------------------------------------+----------------------------------------------------------+
| |Coverage Status on coveralls.io|    | `coveralls.io/r/jedie/IterFilesystem`_                   |
+--------------------------------------+----------------------------------------------------------+
| |Requirements Status on requires.io| | `requires.io/github/jedie/IterFilesystem/requirements/`_ |
+--------------------------------------+----------------------------------------------------------+

.. |Build Status on travis-ci.org| image:: https://travis-ci.org/jedie/IterFilesystem.svg
.. _travis-ci.org/jedie/IterFilesystem: https://travis-ci.org/jedie/IterFilesystem/
.. |Build Status on appveyor.com| image:: https://ci.appveyor.com/api/projects/status/py5sl38ql3xciafc?svg=true
.. _ci.appveyor.com/project/jedie/IterFilesystem: https://ci.appveyor.com/project/jedie/IterFilesystem/history
.. |Coverage Status on codecov.io| image:: https://codecov.io/gh/jedie/IterFilesystem/branch/master/graph/badge.svg
.. _codecov.io/gh/jedie/IterFilesystem: https://codecov.io/gh/jedie/IterFilesystem
.. |Coverage Status on coveralls.io| image:: https://coveralls.io/repos/jedie/IterFilesystem/badge.svg
.. _coveralls.io/r/jedie/IterFilesystem: https://coveralls.io/r/jedie/IterFilesystem
.. |Requirements Status on requires.io| image:: https://requires.io/github/jedie/IterFilesystem/requirements.svg?branch=master
.. _requires.io/github/jedie/IterFilesystem/requirements/: https://requires.io/github/jedie/IterFilesystem/requirements/

-------
Example
-------

Use example CLI, e.g.:

::

    ~$ git clone https://github.com/jedie/IterFilesystem.git
    ~$ cd IterFilesystem
    ~/IterFilesystem$ pipenv install
    ~/IterFilesystem$ pipenv shell
    (IterFilesystem) ~/IterFilesystem$ print_fs_stats --help
    (IterFilesystem) ~/IterFilesystem$ pip install -e .
    ...
    Successfully installed iterfilesystem
    
    ~/IterFilesystem$ $ poetry run print_fs_stats --help
    usage: print_fs_stats.py [-h] [-v] [--debug] [--path PATH]
                             [--skip_dir_patterns [SKIP_DIR_PATTERNS [SKIP_DIR_PATTERNS ...]]]
                             [--skip_file_patterns [SKIP_FILE_PATTERNS [SKIP_FILE_PATTERNS ...]]]
    
    Scan filesystem and print some information
    
    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      --debug               enable DEBUG
      --path PATH           The file path that should be scanned e.g.: "~/foobar/"
                            default is "~"
      --skip_dir_patterns [SKIP_DIR_PATTERNS [SKIP_DIR_PATTERNS ...]]
                            Directory names to exclude from scan.
      --skip_file_patterns [SKIP_FILE_PATTERNS [SKIP_FILE_PATTERNS ...]]
                            File names to ignore.

example output looks like this:

::

    (IterFilesystem) ~/IterFilesystem$ $ print_fs_stats --path ~/IterFilesystem --skip_dir_patterns ".*" "*.egg-info" --skip_file_patterns ".*"
    Read/process: '~/IterFilesystem'...
    Skip directory patterns:
    	* .*
    	* *.egg-info
    
    Skip file patterns:
    	* .*
    
    Filesystem items..:Read/process: '~/IterFilesystem'...
    
    ...
    
    Filesystem items..: 100%|█████████████████████████████████████████|135/135 13737.14entries/s [00:00<00:00, 13737.14entries/s]
    File sizes........: 100%|██████████████████████████████████████████████████████████████|843k/843k [00:00<00:00, 88.5MBytes/s]
    Average progress..: 100%|███████████████████████████████████████████████████████████████████████████████████████|00:00<00:00
    Current File......:, /home/jens/repos/IterFilesystem/Pipfile
    
    
    Processed 135 filesystem items in 0.02 sec
    SHA515 hash calculated over all file content: 10f9475b21977f5aea1d4657a0e09ad153a594ab30abc2383bf107dbc60c430928596e368ebefab3e78ede61dcc101cb638a845348fe908786cb8754393439ef
    File count: 109
    Total file size: 843.5 KB
    6 directories skipped.
    6 files skipped.

-------
History
-------

* `**dev** - compare v1.4.3...master <https://github.com/jedie/IterFilesystem/compare/v1.4.3...master>`_ 

    * TBC

* `16.03.2020 - v1.4.3 <https://github.com/jedie/IterFilesystem/compare/v1.4.2...v1.4.3>`_ 

    * Use logging and remove "verbose mode"

    * Nicer "Average progess" bar

    * Bugfix "Current File" bar: remove comma

* `16.02.2020 - v1.4.2 <https://github.com/jedie/IterFilesystem/compare/v1.4.1...v1.4.2>`_ 

    * iterate over sorted dir entries

    * update CI pipelines

* `02.02.2020 - v1.4.1 <https://github.com/jedie/IterFilesystem/compare/v1.4.0...v1.4.1>`_ 

    * Bugfix ``human_filesize``

* `02.02.2020 - v1.4.0 <https://github.com/jedie/IterFilesystem/compare/v1.3.1...v1.4.0>`_ 

    * ``stats_helper.abort`` exists always usefull to get information if KeyboardInterrupt was used

    * use poetry and modernize project setup

* `20.10.2019 - v1.3.1 <https://github.com/jedie/IterFilesystem/compare/v1.3.0...v1.3.1>`_ 

    * Bugfix if scan directory is completely empty

* `13.10.2019 - v1.3.0 <https://github.com/jedie/IterFilesystem/compare/v1.2.0...v1.3.0>`_ 

    * Set ionice and nice priority via psutils

* `13.10.2019 - v1.2.0 <https://github.com/jedie/IterFilesystem/compare/v1.1.0...v1.2.0>`_ 

    * Refactor API

    * cleanup statistics and process bar

    * handle access errors like: *Permission denied*

    * fix tests

* `12.10.2019 - v1.1.0 <https://github.com/jedie/IterFilesystem/compare/v1.0.0...v1.1.0>`_ 

    * don't create separate process for worker: Just do the work in main process

    * dir/file filter uses now ``fnmatch``

* `12.10.2019 - v1.0.0 <https://github.com/jedie/IterFilesystem/compare/v0.2.0...v1.0.0>`_ 

    * refactoring:

        * don't use ``persist-queue``

        * switch from threading to multiprocessing

        * enhance progress display with multiple ``tqdm`` process bars

* `15.09.2019 - v0.2.0 <https://github.com/jedie/IterFilesystem/compare/v0.1.0...v0.2.0>`_ 

    * store persist queue in temp directory

    * Don't catch ``process_path_item`` errors, this should be made in child class

* `15.09.2019 - v0.1.0 <https://github.com/jedie/IterFilesystem/compare/v0.0.1...v0.1.0>`_ 

    * add some project meta files and tests

    * setup CI

    * fix tests

* `15.09.2019 - v0.0.1 <https://github.com/jedie/IterFilesystem/commit/db89a467a548a969d9d2cdd48adb92114a8833fe>`_ 

    * first Release on PyPi

-----
Links
-----

* `https://pypi.python.org/pypi/IterFilesystem/ <https://pypi.python.org/pypi/IterFilesystem/>`_

* `https://github.com/jedie/IterFilesystem/ <https://github.com/jedie/IterFilesystem/>`_

--------
Donating
--------

* `paypal.me/JensDiemer <https://www.paypal.me/JensDiemer>`_

* `Flattr This! <https://flattr.com/submit/auto?uid=jedie&url=https%3A%2F%2Fgithub.com%2Fjedie%2FIterFilesystem%2F>`_

* Send `Bitcoins <http://www.bitcoin.org/>`_ to `1823RZ5Md1Q2X5aSXRC5LRPcYdveCiVX6F <https://blockexplorer.com/address/1823RZ5Md1Q2X5aSXRC5LRPcYdveCiVX6F>`_

------------

``Note: this file is generated from README.creole 2020-03-16 18:09:30 with "python-creole"``