import os
import zipfile

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from transit_odp.naptan.models import AdminArea, Locality
from transit_odp.organisation.constants import STATUS_CHOICES, FeedStatus
from transit_odp.publish.validators import validate_file_extension


class DatasetPayloadMixin(models.Model):
    STATUS_CHOICES = STATUS_CHOICES

    # TODO - if expiring and expired was removed, then status is really just
    # concerned with / duplicate of the task orchestration status. We probably don't
    # need status at all. I think expiring should be removed and expired should be its
    # own BooleanField.

    upload_file = models.FileField(
        _("Name of the uploaded file, if any"),
        null=True,
        blank=True,
        validators=[validate_file_extension],
    )

    status = FSMField(
        _("Status"),
        choices=STATUS_CHOICES,
        default=FeedStatus.pending.value,
        max_length=20,
        blank=True,
    )

    class Meta:
        abstract = True

    @property
    def is_file_zip(self):
        self.upload_file.seek(0)
        result = zipfile.is_zipfile(self.upload_file)
        self.upload_file.seek(0)
        return result

    @transition(field=status, source="*", target=FeedStatus.pending.value)
    def to_pending(self):
        self.status = FeedStatus.pending.value

    @transition(
        field=status, source=FeedStatus.pending.value, target=FeedStatus.indexing.value
    )
    def to_indexing(self):
        self.status = FeedStatus.indexing.value

    @transition(
        field=status, source=FeedStatus.indexing.value, target=FeedStatus.error.value
    )
    def to_error(self):
        self.status = FeedStatus.error.value

    @transition(
        field=status, source=FeedStatus.indexing.value, target=FeedStatus.success.value
    )
    def to_success(self):
        self.status = FeedStatus.success.value

    @transition(
        field=status, source=FeedStatus.live.value, target=FeedStatus.expiring.value
    )
    def to_expiring(self):
        self.status = FeedStatus.expiring.value

    @transition(
        field=status,
        source=[
            FeedStatus.live.value,
            FeedStatus.success.value,
            FeedStatus.error.value,
            FeedStatus.expiring.value,
        ],
        target=FeedStatus.expired.value,
    )
    def to_expired(self):
        self.status = FeedStatus.expired.value

    @transition(
        field=status,
        source=[
            FeedStatus.live.value,
            FeedStatus.success.value,
            FeedStatus.error.value,
            FeedStatus.expiring.value,
        ],
        target=FeedStatus.inactive.value,
    )
    def to_inactive(self):
        self.status = FeedStatus.inactive.value

    @property
    def upload_file_extension(self):
        if self.upload_file is None:
            return ""
        _, extension = os.path.splitext(self.upload_file.name)
        return extension[1:]


class DatasetPayloadMetadataMixin(models.Model):
    # Likewise for DatasetPayloadMixin, putting all the extracted metadata into its own
    # abstract mixin helps separate the data model. This should likely be its own
    # concrete table related to DatasetPayload.
    # Extracted Metadata
    num_of_lines = models.PositiveIntegerField(_("Lines"), null=True, blank=True)
    num_of_operators = models.PositiveIntegerField(
        _("Number of operators in the feed"), null=True, blank=True
    )
    transxchange_version = models.CharField(max_length=8, blank=True)

    imported = models.DateTimeField(null=True, blank=True)

    # TODO SJB use GeoDjango type
    bounding_box = models.CharField(max_length=8096, null=True, blank=True)

    # Feed creation datetime
    publisher_creation_datetime = models.DateTimeField(null=True, blank=True)
    publisher_modified_datetime = models.DateTimeField(null=True, blank=True)

    first_expiring_service = models.DateTimeField(
        _("Expiry Date"), blank=True, null=True
    )
    last_expiring_service = models.DateTimeField(
        _("Expiry Date"), blank=True, null=True
    )

    first_service_start = models.DateTimeField(_("Start Date"), blank=True, null=True)

    num_of_bus_stops = models.PositiveIntegerField(_("BusStops"), null=True, blank=True)
    num_of_timing_points = models.PositiveIntegerField(
        _("Timing Points"), null=True, blank=True
    )

    admin_areas = models.ManyToManyField(AdminArea, related_name="revisions")
    localities = models.ManyToManyField(Locality, related_name="revisions")

    class Meta:
        abstract = True
