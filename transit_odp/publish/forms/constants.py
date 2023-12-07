from crispy_forms.layout import HTML
from transit_odp.frontend.layout import ButtonSubmit, LinkButton
from django.utils.translation import gettext_lazy as _

NEXT_BUTTON = ButtonSubmit("submit", "submit", content=_("Next step"))
PUBLISH_DATA_BUTTON = ButtonSubmit("submit", "submit", content=_("Upload data"))
SUBMIT_BUTTON = ButtonSubmit("submit", "submit", content=_("Submit"))
SAVE_BUTTON = ButtonSubmit("submit", "submit", content=_("Save"))
PUBLISH_UPDATE_BUTTON = ButtonSubmit("submit", "submit", content=_("Publish changes"))
CONTINUE_BUTTON = ButtonSubmit("submit", "submit", content=_("Continue"))
CANCEL_UPDATE_BUTTON = LinkButton("/", content="Cancel")
CANCEL_PUBLISH_BUTTON = ButtonSubmit("cancel", "cancel", content=_("Cancel"))
CANCEL_PUBLISH_BUTTON.field_classes = "govuk-button govuk-button--secondary"
SEPARATOR = HTML(
    '<hr class="govuk-section-break '
    "           govuk-section-break--xs "
    '           govuk-section-break--visible"'
    ">"
)
EDIT_DESCRIPTION_SUBMIT = ButtonSubmit(
    "submit", "submit", content=_("Save and continue")
)
DISABLE_SUBMIT_SCRIPT = (
    """document.querySelector('form button[type="submit"]').disabled = !this.checked"""
)
