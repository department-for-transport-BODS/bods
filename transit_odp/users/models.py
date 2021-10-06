import invitations.signals
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CASCADE, CharField, ForeignKey, ManyToManyField
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse
from invitations.models import Invitation as InvitationBase

import config.hosts
from transit_odp.bods.interfaces.plugins import get_notifications
from transit_odp.common.validators import validate_profanity
from transit_odp.users.constants import AccountType
from transit_odp.users.managers import InvitationManager
from transit_odp.users.mixins import UserRoleMixin

client = get_notifications()


class User(UserRoleMixin, AbstractUser):
    # First Name and Last Name do not cover name patterns around the globe.
    name = CharField(_("Name of User"), blank=True, max_length=255)

    # Make email required in ./manage.py createsuperuser and else where
    email = models.EmailField(_("email address"), blank=False)
    organisations = ManyToManyField("organisation.Organisation", related_name="users")

    dev_organisation = models.CharField(
        _("Developer organisation"), max_length=55, blank=True
    )

    agent_organisation = models.CharField(
        _("Agent user organisation"), max_length=55, blank=True
    )

    description = models.CharField(
        _("Intended use for the API"), max_length=250, blank=True
    )

    notes = models.CharField(
        _("Notes about a user"),
        max_length=150,
        validators=[validate_profanity],
        blank=True,
    )

    @property
    def pretty_status(self):
        if self.is_active:
            return "Active"
        else:
            return "Inactive"

    @property
    def organisation(self):
        return self.organisations.first()

    @property
    def organisation_id(self):
        if (org := self.organisation) is not None:
            return org.id
        return None

    def get_absolute_url(self):
        # TODO - implement 'public' account view, e.g. '/users/greg/'
        # return reverse("users:detail", kwargs={"username": self.username})
        return None

    def clean(self):
        super().clean()

        if self.is_superuser or self.is_staff:
            # Ensure staff/superusers have site_admin-level access.
            # Note, not all site_admins are staff, i.e. can login to Django admin.
            self.account_type = AccountType.site_admin.value

    def save(self, *args, **kwargs):
        # Calling clean to ensure model is valid since there are many places in Django
        # which do not call clean, e.g.
        #  './manage.py createsuperuser', User.objects.create_user(), etc.
        self.clean()
        super().save(*args, **kwargs)


class Invitation(UserRoleMixin, InvitationBase):
    objects = InvitationManager()
    is_key_contact = models.BooleanField(default=False)

    organisation = ForeignKey(
        "organisation.Organisation",
        on_delete=CASCADE,
        null=True,
        blank=True,
        help_text="The account is tied to this organisation",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.id is None:
            # initialise key (this avoids needing to use InvitationBase.create()
            # which makes using ModelForm, ModelView, etc. really awkward)
            self.key = get_random_string(64).lower()

    def clean(self):
        super().clean()
        # Call mixin validation logic
        super().validate()

    def save(self, *args, **kwargs):
        # ensure clean gets called to validate invitation on save()
        self.clean()
        super().save(*args, **kwargs)

    # Override this method from the InvitationBase to handle multiple hosts.
    # The invitation needs invite_url to bring you back to the correct service
    def send_invitation(self, request, **kwargs):
        invite_url = request.build_absolute_uri(
            reverse("invitations:accept-invite", args=[self.key], host=self.invite_host)
        )
        invite_kwargs = {
            "contact_email": self.email,
            "organisation_name": self.organisation.name,
            "invite_url": invite_url,
        }

        if self.account_type == AccountType.agent_user.value:
            client.send_agent_invite_no_account_notification(**invite_kwargs)
        else:
            client.send_invitation_notification(**invite_kwargs)

        self.sent = now()
        self.save()

        invitations.signals.invite_url_sent.send(
            sender=Invitation,
            instance=self,
            invite_url_sent=invite_url,
            inviter=self.inviter,
        )

    def has_agent_invite(self):
        return hasattr(self, "agent_user_invite")

    @property
    def invite_host(self):
        # The user will be invited to sign up on the given service based on
        # their assigned AccountType
        service_lookup = {
            AccountType.site_admin.value: config.hosts.ADMIN_HOST,
            AccountType.org_admin.value: config.hosts.PUBLISH_HOST,
            AccountType.org_staff.value: config.hosts.PUBLISH_HOST,
            AccountType.agent_user.value: config.hosts.PUBLISH_HOST,
            AccountType.developer.value: config.hosts.DATA_HOST,
        }

        host = service_lookup.get(self.account_type, None)
        if host is None:
            display_type = self.get_account_type_display()
            msg = f"Cannot send invitation for account type {display_type}"
            raise Exception(msg)
        return host


class UserSettings(models.Model):
    user = models.OneToOneField(
        User, related_name="settings", on_delete=models.CASCADE, primary_key=True
    )
    mute_all_dataset_notifications = models.BooleanField(
        _("Mute all feed notifications"), null=False, blank=False, default=False
    )
    notify_invitation_accepted = models.BooleanField(
        _("Team members accept invitation"), null=False, blank=False, default=False
    )
    opt_in_user_research = models.BooleanField(
        _("Opt in for user research"), null=False, blank=False, default=False
    )
    share_app_usage = models.BooleanField(
        _("Share app usage with DFT"), null=False, blank=False, default=False
    )
    notify_avl_unavailable = models.BooleanField(
        _("Published AVL feed unavailable alert"),
        null=False,
        blank=False,
        default=False,
    )


class AgentUserInvite(models.Model):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"
    INACTIVE = "inactive"

    INVITE_STATUS_CHOICES = (
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
        (PENDING, "Pending"),
        (INACTIVE, "Inactive"),
    )
    agent = models.ForeignKey(
        User,
        null=True,
        on_delete=models.deletion.CASCADE,
        related_name="agent_invitations",
    )
    organisation = models.ForeignKey(
        "organisation.Organisation", on_delete=models.deletion.CASCADE
    )
    inviter = models.ForeignKey(
        User,
        on_delete=models.deletion.CASCADE,
        unique=False,
    )

    invitation = models.OneToOneField(
        Invitation,
        on_delete=models.deletion.SET_NULL,
        blank=True,
        null=True,
        default=None,
        related_name="agent_user_invite",
    )
    status = models.CharField(
        choices=INVITE_STATUS_CHOICES,
        default=PENDING,
        null=False,
        blank=False,
        max_length=50,
    )

    @property
    def email(self):
        if self.agent:
            return self.agent.email
        elif self.invitation:
            return self.invitation.email
        else:
            return ""

    @property
    def is_pending(self):
        return self.status == self.PENDING

    @property
    def is_rejected(self):
        return self.status == self.REJECTED

    @property
    def is_accepted(self):
        return self.status == self.ACCEPTED

    @property
    def is_inactive(self):
        return self.status == self.INACTIVE

    @property
    def is_active(self):
        """ An active invite is one that is accepted or pending."""
        return self.status in [self.ACCEPTED, self.PENDING]

    def to_pending(self):
        self.status = self.PENDING
        self.agent.organisations.remove(self.organisation)
        self.save()

    def send_confirmation(self):
        client.send_agent_invite_existing_account_notification(
            self.organisation.name, self.agent.email
        )

    def accept_invite(self):
        """Accept an invitation from an organisation."""
        self.status = self.ACCEPTED
        self.agent.organisations.add(self.organisation)
        self.save()
        client.send_agent_invite_accepted_notification(
            self.organisation.name, self.agent.email
        )
        client.send_operator_agent_accepted_invite_notification(
            self.agent.agent_organisation,
            self.inviter.email,
        )

    def reject_invite(self):
        """Reject an invitation from an organisation."""
        self.status = self.REJECTED
        self.save()
        client.send_agent_invite_rejected_notification(
            self.organisation.name, self.agent.email
        )
        client.send_operator_agent_rejected_invite_notification(
            self.agent.agent_organisation, self.inviter.email
        )

    def remove_agent(self):
        """Remove an agent from an organisation."""
        self.status = self.INACTIVE
        self.agent.organisations.remove(self.organisation)
        self.save()
        client.send_agent_operator_removes_agent_notification(
            self.organisation.name, self.agent.email
        )
        client.send_operator_agent_removed_notification(
            self.agent.agent_organisation, self.inviter.email
        )

    def leave_organisation(self):
        """Leave an organisation."""
        self.status = self.INACTIVE
        self.agent.organisations.remove(self.organisation)
        self.save()
        client.send_agent_leaves_organisation_notification(
            self.organisation.name, self.agent.email
        )
        client.send_operator_agent_leaves_notification(
            self.agent.agent_organisation, self.inviter.email
        )

    def deactivate(self):
        """Deactivate a user invite.
        This should not be used in future, user leave_organisation or
        remove_agent for the most appropriate use case.
        """
        # To leave an organisation
        self.status = self.INACTIVE
        self.agent.organisations.remove(self.organisation)
        self.save()
        client.send_agent_leaves_organisation_notification(
            self.organisation.name, self.agent.email
        )
        client.send_operator_agent_leaves_notification(
            self.agent.agent_organisation, self.inviter.email
        )
