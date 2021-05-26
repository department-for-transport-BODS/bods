from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField

from transit_odp.avl.storage import get_sirivm_storage
from transit_odp.common.fields import CallableStorageFileField
from transit_odp.organisation.models import DatasetRevision
from transit_odp.pipelines.models import TaskResult


class CAVLValidationTaskResult(TaskResult):
    """This model stores the state of the AVL validation workflow"""

    revision = models.ForeignKey(
        DatasetRevision, related_name="+", on_delete=models.CASCADE
    )

    VALID = "FEED_VALID"
    INVALID = "FEED_INVALID"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    ERROR_CHOICES = [
        (VALID, VALID),
        (INVALID, INVALID),
        (SYSTEM_ERROR, SYSTEM_ERROR),
        (TIMEOUT_ERROR, TIMEOUT_ERROR),
    ]
    result = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        choices=ERROR_CHOICES,
        verbose_name=_("Task Result"),
    )

    def to_valid(self):
        self.result = self.VALID
        self.to_success()

    def to_invalid(self):
        self.result = self.INVALID
        self.to_error()

    def to_system_error(self):
        self.result = self.SYSTEM_ERROR
        self.to_error()

    def to_timeout_error(self):
        self.result = self.TIMEOUT_ERROR
        self.to_error()


class CAVLDataArchive(models.Model):
    SIRIVM = "VM"
    GTFSRT = "RT"
    DATA_FORMAT_CHOICES = [(SIRIVM, "Siri VM"), (GTFSRT, "GTFS RT")]

    created = CreationDateTimeField(_("created"))
    last_updated = ModificationDateTimeField(_("last_updated"))
    data = CallableStorageFileField(
        storage=get_sirivm_storage,
        help_text=_("A zip file containing an up to date siri vm XML."),
    )
    data_format = models.CharField(
        max_length=2, choices=DATA_FORMAT_CHOICES, default=SIRIVM
    )

    class Meta:
        get_latest_by = "-created"
        ordering = ("-created",)

    def __repr__(self):

        return (
            f"{self.__class__.__name__}(created={self.created!r}, "
            f"last_updated={self.last_updated!r}, data={self.data.name!r}, "
            f"data_format={self.data_format!r})"
        )
