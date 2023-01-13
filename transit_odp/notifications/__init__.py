from django.conf import settings

from transit_odp.notifications.client import (
    DjangoNotifier,
    GovUKNotifyEmail,
    INotifications,
)


def get_notifications() -> INotifications:
    """
    Returns adapter implementing INotification interface using NOTIFIER setting
    """
    notifiers = {"django": DjangoNotifier, "govuk-notify": GovUKNotifyEmail}
    notifier = getattr(settings, "NOTIFIER", "django")
    notifier_class = notifiers[notifier]
    return notifier_class()
