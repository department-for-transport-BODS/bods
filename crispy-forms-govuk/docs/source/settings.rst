.. _django-crispy-forms: https://github.com/maraujop/django-crispy-forms

========
Settings
========

**crispy-forms-govuk** itself does not have its own settings but overrides some of `django-crispy-forms`_ settings:

CRISPY_ALLOWED_TEMPLATE_PACKS
    To add ``govuk`` template pack name to allowed template packs.
CRISPY_TEMPLATE_PACK
    To set default template pack to ``govuk``.
CRISPY_CLASS_CONVERTERS
    To define some input class name converters required for ``govuk``.

These settings are defined in ``crispy_forms_govuk.settings`` you should have imported (as seen in :ref:`install-intro` document).
