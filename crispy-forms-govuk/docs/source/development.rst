.. _virtualenv: http://www.virtualenv.org
.. _pip: https://pip.pypa.io
.. _Pytest: http://pytest.org
.. _Napoleon: https://sphinxcontrib-napoleon.readthedocs.io
.. _Flake8: http://flake8.readthedocs.io
.. _Sphinx: http://www.sphinx-doc.org
.. _tox: http://tox.readthedocs.io
.. _sphinx-autobuild: https://github.com/GaretJax/sphinx-autobuild
.. _docformatter: https://github.com/myint/docformatter
.. _Mypy: https://mypy.readthedocs.io/en/latest/
.. _Black: https://github.com/python/black
.. _PyFlakes: https://github.com/PyCQA/pyflakes
.. _pycodestyle: https://github.com/PyCQA/pycodestyle
.. _McCabe-script: https://github.com/PyCQA/mccabe

===========
Development
===========

\


Quick Start
===========

Currently only tested on Python 3.6, if Python 3.6 is not your system's default Python 3
interpreter, pass ``PYTHON_INTERPRETER`` in the commands below.

To install the library: ::

    make install PYTHON_INTERPRETER=python3.6

Run tests: ::

    make tests PYTHON_INTERPRETER=python3.6

Run the demo Django app (listening on `<localhost:8002>`_): ::

    make run PYTHON_INTERPRETER=python3.6


Code Quality Tools
==================

Flake8
------

`Flake8`_ is a wrapper around a collection of tools which report styling issues
against the official :PEP:`8` style guide as well as logical errors and code complexity issues.

From the project with the environment activated, run: ::

    flake8

The error codes of flake8 are:

* E***/W***: Detections of `pycodestyle`_ (Errors and warnings against PEP8 style guide guide)
* F***: Detections of `PyFlakes`_ (logical errors)
* C9**: Detections of `McCabe-script`_ (complexity warnings)


Black
-----

`Black`_ is an autoformatter which fixes many of the linting errors reported by `Flake8`_
as well as frees up time spent on hand-formatting code.

From the project directory, run: ::

    black .


docformatter
------------

`docformatter`_ is a tool which formats docstrings
(currently not handled by `Black`_, see `issue <https://github.com/python/black/issues/144>`_)
to follow :PEP:`257` conventions.

From the project directory, run: ::

     docformatter -ir --wrap-summaries 88 --wrap-descriptions 88 .


Mypy
----

`Mypy`_ is a static type checker.

To run, from the project directory, execute: ::

    mypy .

Testing
=======

The project uses the `Pytest`_ framework and only targets Python 3.6.

To run the tests: ::

    make install PYTHON_INTERPRETER=python3.6
    make tests PYTHON_INTERPRETER=python3.6


Documentation
=============

To generate the `Sphinx`_ documentation, ensure the environment is activated, then from the `docs`
directory run: ::

    make html

This will produce `build/html/index.html` which can be opened in the browser.
