from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from transit_odp.changelog.constants import KnownIssueCategory, KnownIssueStatus


class KnownIssues(TimeStampedModel):
    description = models.TextField(_("Description"), null=False, blank=False)
    category = models.CharField(
        _("Category"),
        max_length=20,
        choices=KnownIssueCategory.choices,
        null=False,
        blank=False,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=KnownIssueStatus.choices,
        null=False,
        blank=False,
        default=KnownIssueStatus.PENDING.value,
    )
    deleted = models.BooleanField(_("Deleted"), default=False)

    def __str__(self):
        return self.description


class HighLevelRoadMap(TimeStampedModel):
    class Meta:
        verbose_name = "High Level Road Map"
        verbose_name_plural = "High Level Road Map"

    description = models.TextField(_("Description"), null=False, blank=False)
