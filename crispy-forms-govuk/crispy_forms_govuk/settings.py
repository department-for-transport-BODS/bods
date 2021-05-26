"""
Settings
========

Default required settings. You can override them in your project settings
file.
"""

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_ALLOWED_TEMPLATE_PACKS = (
    "bootstrap",
    "uni_form",
    "bootstrap3",
    "bootstrap4",
    "govuk",
)

CRISPY_TEMPLATE_PACK = "govuk"

CRISPY_CLASS_CONVERTERS = {
    "textinput": "govuk-input ",
    "hiddeninput": "",
    "urlinput": "govuk-input ",
    "numberinput": "govuk-input ",
    "emailinput": "govuk-input ",
    "dateinput": "govuk-input govuk-date-input__input ",
    "textarea": "govuk-textarea ",
    "passwordinput": "govuk-input ",
    "fileinput": "govuk-file-upload",
    "clearablefileinput": "govuk-file-upload",
    "select": "govuk-select ",
    "checkboxinput": "govuk-checkboxes__input ",
    "radioinput": "govuk-radios__input ",
    # 'button': "govuk-button ",
}
