from django.conf import settings
from django.utils.module_loading import import_string

from transit_odp.bods.interfaces.gateways import ICAVLService
from transit_odp.bods.interfaces.notifications import INotifications
from transit_odp.notifications.client import DjangoNotifier, GovUKNotifyEmail


def get_cavl_service() -> ICAVLService:
    """
    Returns adapter implementing the ICAVLService interface using CAVL_SERVICE setting
    """
    try:
        return import_string(settings.CAVL_SERVICE)()
    except ImportError as e:
        msg = "Could not import '%s' for API setting 'CAVL_SERVICE'. %s: %s." % (
            settings.CAVL_SERVICE,
            e.__class__.__name__,
            e,
        )
        raise ImportError(msg)


def get_notifications() -> INotifications:
    """
    Returns adapter implementing INotification interface using NOTIFIER setting
    """
    notifiers = {"django": DjangoNotifier, "govuk-notify": GovUKNotifyEmail}
    notifier = getattr(settings, "NOTIFIER", "django")
    notifier_class = notifiers[notifier]
    return notifier_class()
