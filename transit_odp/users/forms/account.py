from crispy_forms.helper import Layout
from crispy_forms.layout import HTML
from crispy_forms_govuk.forms import GOVUKModelForm
from crispy_forms_govuk.layout import ButtonSubmit
from django import forms
from django.utils.translation import gettext as _

from transit_odp.users.models import UserSettings

INVITATION_NOTIFY = "notify_invitation_accepted"
AVL_NOTIFY = "notify_avl_unavailable"


class PublishAdminNotifications(GOVUKModelForm):
    class Meta:
        model = UserSettings
        fields = (INVITATION_NOTIFY, AVL_NOTIFY)

    notify_invitation_accepted = forms.BooleanField(required=False)
    notify_avl_unavailable = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.user.is_org_admin:
            notify_invitation_accepted = self.fields[INVITATION_NOTIFY]
            notify_invitation_accepted.label = "Team members accept invitation"
        else:
            # Agents/Standard users shouldn't get invitation notifications
            self.fields.pop(INVITATION_NOTIFY)

        notify_avl_unavailable = self.fields[AVL_NOTIFY]
        notify_avl_unavailable.label = "Published feed data unavailable alert"
        notify_avl_unavailable.help_text = (
            "Receive an email if data is not received from your AVL feed for more than "
            "5 minutes "
        )

        self.heading = HTML('<h3 class="govuk-heading-m">Notification settings</h3>')
        self.hint = HTML(
            (
                '<span class="govuk-hint">'
                "Choose what you would like to receive below. Allow up to 24 hours "
                "for any changes to take effect."
                "</span>"
            )
        )
        self.save_button = ButtonSubmit(content=_("Save"))

    def get_layout(self):
        return Layout(
            self.heading,
            self.hint,
            AVL_NOTIFY,
            INVITATION_NOTIFY,
            self.save_button,
        )
