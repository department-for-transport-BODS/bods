from django.utils.crypto import get_random_string
from invitations.managers import BaseInvitationManager


class InvitationManager(BaseInvitationManager):
    def create(self, email, inviter=None, key=None, **kwargs):
        # Note - this replaces the create method defined on
        # invitations.models.Invitation as it doesn't play nice
        # with ModelForm, ModelView, DjangoFactory, etc. classes
        if key is None:
            key = get_random_string(64).lower()
        return super().create(email=email, inviter=inviter, key=key, **kwargs)
