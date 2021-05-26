# Signals that fires when a user logs in and logs out

from django.contrib.auth import user_logged_out
from django.dispatch import receiver

from transit_odp.restrict_sessions.models import LoggedInUser


@receiver(user_logged_out)
def on_user_logged_out(sender, **kwargs):
    LoggedInUser.objects.filter(user=kwargs.get("user")).delete()
