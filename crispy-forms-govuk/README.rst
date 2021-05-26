.. _Django: https://www.djangoproject.com/
.. _django-crispy-forms: https://github.com/maraujop/django-crispy-forms
.. _GovUK Design System: https://design-system.service.gov.uk/

Introduction
============

This is a `Django`_ application to add `django-crispy-forms`_ layout objects for the `GovUK Design System`_.



Development
-----------

Currently only tested on Python 3.6, if Python 3.6 is not your system's default Python 3
interpreter, pass ``PYTHON_INTERPRETER`` in the commands below.

To install the library: ::

    make install PYTHON_INTERPRETER=python3.6

Run tests: ::

    make tests PYTHON_INTERPRETER=python3.6

Run the demo Django app (listening on `<localhost:8002>`_): ::

    make run PYTHON_INTERPRETER=python3.6
