from django import forms
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.db.models.functions.text import Substr, Upper
from django.utils.translation import gettext_lazy as _
from invitations.utils import get_invitation_model

from transit_odp.organisation.constants import ORG_PENDING_INVITE
from transit_odp.site_admin.forms.base import CheckboxFilterForm
from transit_odp.users.constants import AgentUserType, DeveloperType
from transit_odp.crispy_forms_govuk.forms import GOVUKModelForm

User = auth.get_user_model()
Invitation = get_invitation_model()


class BulkResendInvitesForm(forms.Form):
    form_method = "get"
    bulk_invite = forms.BooleanField(required=False, initial=False)
    invites = forms.IntegerField(required=False)

    def __init__(self, *args, orgs=None, **kwargs):
        self.orgs_qs = orgs
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.data.get("bulk_invite", False) and not self.data.getlist("invites"):
            raise ValidationError(
                _("Please select organisation(s) from below to resend invitation")
            )

    def clean_invites(self):
        org_ids = [int(org_id) for org_id in self.data.getlist("invites", [])]
        return org_ids

    def _post_clean(self):
        if (
            self.orgs_qs.filter(id__in=self.cleaned_data["invites"])
            .exclude(status=ORG_PENDING_INVITE)
            .exists()
        ):
            self.add_error(
                None,
                ValidationError(
                    _(
                        "You cannot send invites to already active organisations, "
                        "please select pending ones"
                    )
                ),
            )


class EditNotesForm(GOVUKModelForm):
    class Meta:
        model = User
        fields = ["notes"]
        labels = {"notes": "Notes"}
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 5, "cols": 20}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ConsumerFilterForm(CheckboxFilterForm):
    form_label = "Email"

    def get_queryset(self):
        return User.objects.filter(account_type=DeveloperType).annotate(
            first_letter=Upper(Substr("email", 1, 1))
        )


class AgentOrganisationFilterForm(CheckboxFilterForm):
    form_label = "Agents"

    def get_queryset(self):
        return User.objects.filter(account_type=AgentUserType).annotate(
            first_letter=Upper(Substr("agent_organisation", 1, 1))
        )
