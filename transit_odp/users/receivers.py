import logging

from allauth.account.models import EmailConfirmation
from allauth.account.signals import (
    email_confirmation_sent,
    password_changed,
    password_reset,
)
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token

from transit_odp.notifications import get_notifications
from transit_odp.users.constants import AccountType
from transit_odp.users.models import Invitation, User, UserSettings
from transit_odp.users.signals import user_accepted

logger = logging.getLogger(__name__)
client = get_notifications()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_settings(sender, instance=None, created=False, **kwargs):
    if created:
        UserSettings.objects.create(user=instance)


@receiver(user_accepted)
def notify_on_accepted_invite(invite: Invitation, user: User, **kwargs):
    inviter = invite.inviter
    assert (
        inviter.account_type == AccountType.site_admin.value
        or inviter.organisation in list(user.organisations.all())
    ), "New user and inviter are not in same organisation"

    if user.account_type == AccountType.agent_user.value:
        client.send_agent_invite_accepted_notification(
            invite.organisation.name, user.email
        )

    if not inviter.settings.notify_invitation_accepted:
        return

    if user.account_type == AccountType.agent_user.value:
        client.send_operator_agent_accepted_invite_notification(
            user.agent_organisation, invite.inviter.email
        )

    else:
        client.send_invite_accepted_notification(
            inviter_email=inviter.email,
            invitee_email=user.email,
            organisation_name=inviter.organisation.name,
        )


@receiver(email_confirmation_sent, sender=EmailConfirmation)
def delete_previous_email_confirmations(
    sender, request, confirmation, signup, **kwargs
):
    """Deletes any previous EmailConfirmations sent by the user. Thus, making only the
    most recent 'valid'.

    This receiver listens to django-allauth's email_confirmation_sent signal and deletes
    any other EmailConfirmation
    objects for that email_address. This means any old email confirmation links sent to
    the user will not be valid.

    See https://itoworld.atlassian.net/browse/BODP-519
    - Verification emails should become invalid when superseded by an new email
    """
    logger.info(
        "[delete_previous_email_confirmations] called - deleting existing confirmation "
        "emails"
    )
    confirmation.email_address.emailconfirmation_set.exclude(
        id=confirmation.id
    ).delete()


@receiver(m2m_changed, sender=User.organisations.through)
def check_added_organisation_change(sender, instance, action, **kwargs):
    if action == "pre_add":
        if not instance.is_org_user:
            raise ValidationError(
                _("Invalid organisation for account_type. Please contact support.")
            )

        if instance.is_single_org_user:
            if instance.organisations.count() > 0:
                raise ValidationError(
                    _(
                        "Organisation user can only have one organisation. "
                        "Please contact support."
                    )
                )


@receiver(password_changed)
def notify_on_password_change(request, user, **kwargs):
    client.send_password_change_notification(user.email)


@receiver(password_reset)
def notify_on_password_reset(request, user, **kwargs):
    client.send_password_change_notification(user.email)
