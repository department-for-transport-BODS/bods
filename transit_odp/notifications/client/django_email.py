import logging
from typing import Dict

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from transit_odp.notifications.client.base import NotificationBase
from transit_odp.notifications.constants import TEMPLATE_LOOKUP

logger = logging.getLogger(__name__)


class DjangoNotifier(NotificationBase):
    def __init__(self):
        super().__init__()
        self.subject_prefix = getattr(settings, "EMAIL_SUBJECT_PREFIX", "[BODS]")
        self.from_email = getattr(
            settings, "DEFAULT_FROM_EMAIL", "Bus Open Data Service <noreply@bods.com>"
        )

    def _send_mail(self, template: str, email: str, **kwargs):
        """
        :param template: path to template
        :param email: address to send email to
        :param subject: email subject, defaulted to key of template dict
        :param kwargs: the remaining kwargs are render template variables
        :return:
        """
        template_path = self.templates[template]
        default_subject = template.title().replace("_", " ")
        subject = kwargs.pop("subject", default_subject)
        subject = f"{self.subject_prefix}{subject}"
        body = render_to_string(template_path, kwargs)

        send_mail(subject, body, self.from_email, [email])

    @property
    def templates(self) -> Dict[str, str]:
        return TEMPLATE_LOOKUP
