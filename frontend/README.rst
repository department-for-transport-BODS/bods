.. _Django: https://www.djangoproject.com/
.. _django-crispy-forms: https://github.com/maraujop/django-crispy-forms
.. _GovUK Design System: https://design-system.service.gov.uk/

Introduction
============

This is a `Django`_ application which integrates a Gulp-based asset
pipeline into the BODDS project. This allows us to compile JS, SCSS, etc.
and install `GovUK Design System`_ assets into the Django app at build time.


Quick start
-----------

1. Add "frontend" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'frontend',
    ]


Development
-----------

Install node packages: ::

     npm install

To compile (and watch) frontend assets run: ::

    gulp watch

or to do a one-time build run: ::

    gulp build


Testing
-------
