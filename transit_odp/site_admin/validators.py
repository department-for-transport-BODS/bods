from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from transit_odp.users.models import Invitation


def validate_email_unique(email: str) -> None:
    if Invitation.objects.filter(email=email).exists():
        raise ValidationError(message=_(f"{email} has been already invited."))
