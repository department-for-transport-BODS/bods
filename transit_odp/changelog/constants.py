from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class KnownIssueStatus(TextChoices):
    PENDING = ("pending", _("Pending"))
    FIXED = ("fixed", _("Fixed"))


class KnownIssueCategory(TextChoices):
    CONSUMER = ("consumer", _("Consumer"))
    PUBLISHER = ("publisher", _("Publisher"))


PendingStatus = KnownIssueStatus.PENDING.value
FixedStatus = KnownIssueStatus.FIXED.value

ConsumerIssue = KnownIssueCategory.CONSUMER.value
PublisherIssue = KnownIssueCategory.PUBLISHER.value
