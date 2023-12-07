from crispy_forms.layout import ButtonHolder, Layout
from transit_odp.frontend.forms import GOVUKForm
from transit_odp.frontend.layout.buttons import ButtonSubmit, LinkButton
from django.utils.translation import gettext_lazy as _

GOV_BUTTON_SECONDARY_CLASS = "govuk-button govuk-button--secondary"


class ConfirmationForm(GOVUKForm):
    def __init__(self, cancel_url, *args, label="Confirm", **kwargs):
        super().__init__(*args, **kwargs)
        self.label = label
        self.cancel_url = cancel_url

    def get_layout(self):
        cancel_link_button = LinkButton(url=self.cancel_url, content="Cancel")
        cancel_link_button.field_classes = GOV_BUTTON_SECONDARY_CLASS

        return Layout(
            ButtonHolder(
                ButtonSubmit("submit", "submit", content=_(self.label)),
                cancel_link_button,
            )
        )


class AcceptRejectForm(GOVUKForm):
    def get_layout(self):
        accept_button = ButtonSubmit("status", "accepted", content=_("Accept"))
        reject_button = ButtonSubmit("status", "rejected", content=_("Reject"))
        reject_button.field_classes = GOV_BUTTON_SECONDARY_CLASS
        return ButtonHolder(Layout(accept_button, reject_button))


class AgentLeaveForm(GOVUKForm):
    def get_layout(self):
        confirm_button = ButtonSubmit("status", "inactive", content=_("Confirm"))
        cancel_button = ButtonSubmit("status", "", content=_("Cancel"))
        cancel_button.field_classes = GOV_BUTTON_SECONDARY_CLASS
        return ButtonHolder(Layout(confirm_button, cancel_button))


class AgentRemoveForm(AgentLeaveForm):
    pass


class AgentResendInviteForm(GOVUKForm):
    def get_layout(self):
        confirm_button = ButtonSubmit("submit", "resend", content=_("Confirm"))
        cancel_button = ButtonSubmit("submit", "cancel", content=_("Cancel"))
        cancel_button.field_classes = GOV_BUTTON_SECONDARY_CLASS
        return ButtonHolder(Layout(confirm_button, cancel_button))


class ConfirmCancelForm(GOVUKForm):
    def get_layout(self):
        confirm_button = ButtonSubmit("submit", "confirm", content=_("Confirm"))
        cancel_button = ButtonSubmit("submit", "cancel", content=_("Cancel"))
        cancel_button.field_classes = GOV_BUTTON_SECONDARY_CLASS
        return ButtonHolder(Layout(confirm_button, cancel_button))
