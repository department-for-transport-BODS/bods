from django.shortcuts import render
from invitations.app_settings import app_settings
from invitations.views import AcceptInvite as AcceptInviteBase

from transit_odp.users.views.mixins import AdapterMixin


class AcceptInvite(AdapterMixin, AcceptInviteBase):
    """Extends django-invitations' AcceptInvite view to do extra
    initialisation of the flow"""

    def post(self, *args, **kwargs):
        self.object = invitation = self.get_object()
        if app_settings.GONE_ON_ACCEPT_ERROR and (
            not invitation
            or (invitation and (invitation.accepted or invitation.key_expired()))
        ):
            return render(
                self.request,
                "users/invitation_expired.html",
                context=self.context_object_name,
            )

        # reset invitation_started - this is switched on by SignupView to prevent
        # multiple GETs
        self.adapter.unstash_invitation_started(self.request)
        return super().post(*args, **kwargs)
