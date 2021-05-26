.. _django-bodp: https://gitlab01.itoworld.internal/transit-hub/bodp-django
.. _django-crispy-forms: https://github.com/maraujop/django-crispy-forms

.. _install-intro:

=======
Install
=======

Currently this library lives as a subproject of `django-bodp`_ and is not distributed via PyPI.

#. Install locally: ::

    pip install -e ./crispy-forms-govuk


#. Register app in your project settings:

    .. sourcecode:: python

        INSTALLED_APPS = (
            ...
            'crispy_forms',
            'crispy_forms_govuk',
            ...
        )

#. Import default settings at the end of the settings file:

    .. sourcecode:: python

        from crispy_forms_govuk.settings import *

    All other `django-crispy-forms`_ settings option apply, see its documentation for more details.

#. You will need to install GOV.UK assets in your project. See `Getting Started <https://design-system.service.gov.uk/get-started/production/>`_.
