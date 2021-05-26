import logging

from transit_odp.users.models import Invitation

logger = logging.getLogger(__name__)


def notify_user_accepted_invitation(user):
    try:
        invitation = Invitation.objects.get(email=user.email)
    except Invitation.DoesNotExist:
        logger.debug(
            f"[notify_user_accepted] user {user.email} created without invitation"
        )
        return

    inviter = invitation.inviter
    logger.debug(
        f"[notify_user_accepted] notifying inviter {inviter.email} that "
        f"user {user.email} has accepted invitation"
    )

    if inviter.settings.notify_invitation_accepted:
        invitation.send_invitation_accepted()
