import hashlib
import logging
import os
from typing import Optional, cast

from django.conf import settings
from django.contrib.postgres.fields.array import ArrayField
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Index, Q, UniqueConstraint
from django.db.models.functions import Length
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from django_hosts import reverse
from model_utils import FieldTracker

from config import hosts
from transit_odp.avl.client import CAVLService
from transit_odp.avl.constants import COMPLIANCE_STATUS_CHOICES, UNDERGOING
from transit_odp.avl.enums import AVLFeedStatus
from transit_odp.common.validators import validate_profanity
from transit_odp.organisation import signals
from transit_odp.organisation.constants import (
    DATASET_TYPE_NAMESPACE_MAP,
    DATASET_TYPE_PRETTY_MAP,
    DatasetType,
    FeedStatus,
)
from transit_odp.organisation.managers import (
    DatasetManager,
    DatasetRevisionManager,
    SeasonalServiceManager,
    ServiceCodeExemptionManager,
)
from transit_odp.organisation.mixins import (
    DatasetPayloadMetadataMixin,
    DatasetPayloadMixin,
)
from transit_odp.organisation.querysets import (
    DatasetRevisionQuerySet,
    TXCFileAttributesQuerySet,
)
from transit_odp.pipelines.signals import dataset_etl
from transit_odp.timetables.dataclasses.transxchange import TXCFile
from transit_odp.users.models import User

logger = logging.getLogger(__name__)

# Register database Length transformation as query lookup
#  see https://docs.djangoproject.com/en/1.11/ref/models/database-functions/#length
models.FileField.register_lookup(Length, "length")


class Dataset(TimeStampedModel):
    # attribute set dynamically by select_related_live_revision QS method
    _live_revision: Optional[DatasetRevisionQuerySet]

    organisation = models.ForeignKey(
        "Organisation",
        on_delete=models.CASCADE,
        help_text="Bus portal organisation.",
    )

    live_revision = models.OneToOneField(
        "DatasetRevision",
        on_delete=models.SET_NULL,
        null=True,
        related_name="live_revision_dataset",
    )

    contact = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="This user will receive all notifications",
        related_name="created_datasets",
        null=False,
        blank=False,
    )

    subscribers = models.ManyToManyField(
        User, through="DatasetSubscription", related_name="subscriptions"
    )

    dataset_type = models.IntegerField(
        choices=DatasetType.choices(), default=DatasetType.TIMETABLE
    )

    avl_feed_status = models.CharField(
        help_text="The operational status of the AVL Feed stream processor",
        blank=True,
        default="",
        choices=AVLFeedStatus.choices(),
        max_length=20,
    )
    avl_feed_last_checked = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The time when the AVL feed status was last checked",
    )

    is_dummy = models.BooleanField(default=False, null=False, blank=False)

    objects = DatasetManager()

    def __str__(self):
        return f"id={self.id!r}, dataset_type={DatasetType(self.dataset_type).name!r}"

    @property
    def download_url(self) -> str:
        """Returns the URL to where the dataset can be downloaded
        currently there are only endpoints for fares and timetables.
        If this is called for location data then reverse will raise.
        Leaving this in for now as we probably want to know if this happens"""

        view_namespace = DATASET_TYPE_NAMESPACE_MAP[self.dataset_type]

        download_view_name = "feed-download"
        download_view_name = (
            f"{view_namespace}-{download_view_name}"
            if view_namespace
            else download_view_name
        )
        return reverse(download_view_name, host=hosts.DATA_HOST, args=[self.id])

    @property
    def feed_detail_url(self) -> str:
        """Returns the URL of where the user goes after clicking on a dataset.
        ie if the dataset is published the feed-detail URL is returned otherwise
        the review page is returned"""

        view_namespace = DATASET_TYPE_NAMESPACE_MAP[self.dataset_type]
        view_name = "feed-detail" if self.live_revision else "revision-publish"
        view_name = f"{view_namespace}:{view_name}" if view_namespace else view_name
        org_id = self.organisation.id
        dataset_id = self.id

        return reverse(
            view_name,
            kwargs={"pk": dataset_id, "pk1": org_id},
            host=hosts.PUBLISH_HOST,
        )

    @property
    def get_is_published(self):
        return self.live_revision and self.live_revision.is_published

    @property
    def pretty_dataset_type(self):
        return DATASET_TYPE_PRETTY_MAP[self.dataset_type]

    @property
    def is_remote(self):
        return self.live_revision and self.live_revision.url_link != ""

    @property
    def is_local(self):
        return self.live_revision and self.live_revision.url_link == ""

    def get_hash(self):
        return self.live_revision and self.live_revision.get_hash()

    def compute_hash(self, data):
        return self.live_revision and self.live_revision.compute_hash(data)

    def get_file_content(self) -> Optional[bytes]:
        return self.live_revision and self.live_revision.get_file_content()

    def get_availability_retry_count(self) -> Optional[bytes]:
        return self.live_revision and self.live_revision.get_availability_retry_count()

    def start_revision(self, name=None, **kwargs):
        """Start a new revision"""
        # name is always initialised to None as it gets assigned a temporary name
        # in the save method. If name is
        #  provided it overrides the temporary name
        defaults = kwargs
        if self.live_revision is None:
            # Set defaults for first revision
            defaults = {"comment": "First publication"}
            defaults.update(kwargs)
        else:
            # Set defaults for subsequent revisions
            defaults = {
                "description": self.live_revision.description,
                "short_description": self.live_revision.short_description,
                # "comment": self.live_revision.comment,  # GB: don't copy the comment
                "upload_file": self.live_revision.upload_file,
                "url_link": self.live_revision.url_link,
            }
            defaults.update(kwargs)

        return DatasetRevision(dataset=self, name=name, **defaults)


class DatasetSubscription(TimeStampedModel):
    class Meta:
        unique_together = ("dataset", "user")

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class DatasetRevision(
    DatasetPayloadMixin, DatasetPayloadMetadataMixin, TimeStampedModel
):
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        help_text="The parent dataset",
        related_name="revisions",
    )

    name = models.CharField(
        _("Feed name"), max_length=255, validators=[validate_profanity], unique=True
    )

    description = models.CharField(
        _("Any description for the feed"),
        max_length=255,
        validators=[validate_profanity],
    )

    short_description = models.CharField(
        _("Short description for the feed"),
        max_length=30,
        validators=[validate_profanity],
    )

    comment = models.CharField(
        _("Any comments for the feed"),
        max_length=255,
        blank=True,
        validators=[validate_profanity],
    )

    url_link = models.URLField(
        _("URL link to feed, if any"), max_length=500, blank=True
    )

    # TODO - remove redundant column & use annotation derived from published_at
    is_published = models.BooleanField(
        default=False, help_text="Whether the feed is published or not"
    )

    published_at = models.DateTimeField(
        null=True, blank=True, help_text="The time when this change was published"
    )

    # TODO - add System users, e.g. Celery, so we can make this column null=False
    published_by = models.ForeignKey(
        User,
        related_name="publications",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        help_text="The user that made this change",
    )

    last_modified_user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        help_text="Bus portal organisation.",
    )

    username = models.CharField(
        _("Username required to access the resource, if any"),
        max_length=255,
        blank=True,
    )

    password = models.CharField(
        _("Password required to access the resource, if any"),
        max_length=255,
        blank=True,
    )
    requestor_ref = models.CharField(
        _("Requestor ref to access the resource, if any"), max_length=255, blank=True
    )

    objects = DatasetRevisionManager()
    tracker = FieldTracker()

    class Meta(TimeStampedModel.Meta):
        ordering = ("name",)
        constraints = [
            # This constraint ensures that each revision has unique natural
            # key: dataset-created
            UniqueConstraint(
                fields=["dataset", "created"],
                name="organisation_datasetrevision_unique_revision",
            ),
            # This constraint ensures that each dataset only has one
            # unpublished revision
            UniqueConstraint(
                fields=["dataset"],
                condition=Q(is_published=False),
                name="organisation_datasetrevision_unique_draft_revision",
            ),
        ]
        indexes = [Index(fields=["is_published"])]

    def __str__(self):
        return f"id={self.id}, dataset_id={self.dataset_id}, name={self.name}"

    def save(self, **kwargs):
        if self.name is None or self.name == "":
            self.set_temporary_name()
        super().save(**kwargs)

    def start_etl(self):
        """Signals to ETL pipeline to index the dataset"""
        # TODO - factor this out into a PipelineService
        if self.dataset.dataset_type == DatasetType.TIMETABLE.value:
            dataset_etl.send(self, revision=self)

    def get_availability_retry_count(self):
        """Returns availability_retry_count initialising the model if
        it doesn't exist"""
        from transit_odp.pipelines.models import RemoteDatasetHealthCheckCount

        # TODO - refactor this into a post-save signal to create the
        # RemoteDatasetHealthCheckCount when a revision is created. Also, probably
        # only need one health check per Dataset?
        try:
            retry_count = self.availability_retry_count
        except DatasetRevision.availability_retry_count.RelatedObjectDoesNotExist:
            # create counter if it doesn't exist
            retry_count = RemoteDatasetHealthCheckCount(revision=self)
            retry_count.save()

        return retry_count

    @property
    def has_pti_result(self):
        return hasattr(self, "pti_result")

    def is_pti_compliant(self):
        """
        Returns if a DatasetRevision is PTI compliant.
        """
        if self.modified.date() < settings.PTI_START_DATE.date():
            return False

        if self.has_pti_result:
            return self.pti_result.is_compliant

        return self.pti_observations.count() == 0

    def publish(self, user=None):
        """Publish the revision"""
        if not self.is_published:
            now = timezone.now()
            # TODO - should likely fold the logic in 'update_live_revision' receiver
            # into this method, i.e. update live_revision on the dataset to point to
            # this newly published revision in an atomic transaction.
            #  However, then tests wouldn't be as easy to initialise / be data-driven
            # TODO - remove 'live' status
            if self.status == FeedStatus.success.value:
                self.status = FeedStatus.live.value
            self.is_published = True
            self.published_at = now
            self.published_by = user

            # register AVL dataset with CAVL
            if self.dataset.dataset_type == DatasetType.AVL:
                cavl_service = CAVLService()

                # if the Dataset is brand new then we must register the feed
                # with CAVL, else we must update
                is_new = self.dataset.live_revision_id is None

                if is_new:
                    cavl_service.register_feed(
                        feed_id=self.dataset.id,
                        publisher_id=cast(int, self.dataset.organisation_id),
                        url=self.url_link,
                        username=self.username,
                        password=self.password,
                    )
                else:
                    cavl_service.update_feed(
                        feed_id=self.dataset.id,
                        url=self.url_link,
                        username=self.username,
                        password=self.password,
                    )

            self.save()
            signals.revision_publish.send(self, dataset=self.dataset)

    def publish_error(self, user=None):
        """Publish an error revision; used in monitoring endpoints"""
        if not self.is_published:
            now = timezone.now()
            # TODO - should likely fold the logic in 'update_live_revision' receiver
            # into this method, i.e. update
            #  live_revision on the dataset to point to this newly published revision
            # in an atomic transaction.
            #  However, then tests wouldn't be as easy to initialise / be data-driven
            # TODO - remove 'live' status
            self.status = FeedStatus.error.value
            self.is_published = True
            self.published_at = now
            self.published_by = user
            self.save()

    # Associate a file on the local file system with the upload_file property.
    def associate_file(self, filepath: str):
        with open(filepath, "rb") as fin:
            # Get the filename from the path
            _, filename = os.path.split(filepath)

            content_file = ContentFile(fin.read())
            self.upload_file.save(filename, content_file)

    def log_error(self, message: str):
        # Deprecated. Convert all errors to use new associated_errors mechanism
        pass

    # TODO - remove this
    @property
    def is_public(self):
        # return FeedStatus[self.status].is_public()
        return self.is_published

    @property
    def is_remote(self):
        return self.url_link != ""

    @property
    def is_local(self):
        return self.url_link == ""

    @property
    def draft_url(self):
        """returns either the draft review url if the revision is not published
        or the feed detail page if it is"""
        # Remember a dataset can only have one draft revision
        dataset = self.dataset
        dataset_id = dataset.id
        org_id = dataset.organisation.id

        view_namespace = DATASET_TYPE_NAMESPACE_MAP[dataset.dataset_type]
        view_namespace = view_namespace + ":" if view_namespace else view_namespace

        if not dataset.live_revision:
            # the dataset is new and this is its draft revision
            view_name = view_namespace + "revision-publish"

        elif dataset.live_revision != self:
            # the dataset has been modified but changes are unpublished
            view_name = view_namespace + "revision-update-publish"

        else:
            # this revision has been published and is now live
            # probably an old link
            view_name = view_namespace + "feed-detail"

        return reverse(
            view_name,
            kwargs={"pk": dataset_id, "pk1": org_id},
            host=hosts.PUBLISH_HOST,
        )

    @property
    def report_url(self):
        """returns draft's validtion report url review url"""
        if self.dataset.dataset_type == DatasetType.TIMETABLE:
            dataset = self.dataset
            dataset_id = dataset.id
            org_id = dataset.organisation.id

            view_namespace = DATASET_TYPE_NAMESPACE_MAP[dataset.dataset_type]
            view_name = "review-pti-csv"
            view_name = f"{view_namespace}:{view_name}" if view_namespace else view_name

            return reverse(
                view_name,
                kwargs={"pk": dataset_id, "pk1": org_id},
                host=hosts.PUBLISH_HOST,
            )
        return ""

    @property
    def post_schema_report_url(self):
        """returns draft's validtion report url review url"""
        if self.dataset.dataset_type == DatasetType.TIMETABLE:
            dataset = self.dataset
            dataset_id = dataset.id
            org_id = dataset.organisation.id

            view_namespace = DATASET_TYPE_NAMESPACE_MAP[dataset.dataset_type]
            view_name = "review-post-schema-csv"
            view_name = f"{view_namespace}:{view_name}" if view_namespace else view_name

            return reverse(
                view_name,
                kwargs={"pk": dataset_id, "pk1": org_id},
                host=hosts.PUBLISH_HOST,
            )
        return ""

    def get_hash(self):
        """Returns the hash of the currently cached dataset"""
        file_content = self.get_file_content()

        if file_content is not None:
            return self.compute_hash(file_content)

    def compute_hash(self, data):
        """Algorithm for computing checksum of data"""
        return hashlib.sha1(data).hexdigest()

    def get_file_content(self) -> Optional[bytes]:
        """Returns the content of the locally cached dataset as bytes"""
        if self.upload_file is not None:
            with self.upload_file.open("rb") as fin:
                return fin.read()
        return None

    def set_temporary_name(self) -> None:
        """
        Creates a temporary name for the DatasetRevision.
        """
        now = timezone.localtime()
        org_name = self.dataset.organisation.name
        dataset_id = self.dataset.id
        self.name = f"{org_name}_{dataset_id}_{now:%Y%m%d %H:%M:%S}"


class DatasetMetadata(models.Model):
    revision = models.OneToOneField(
        DatasetRevision, related_name="metadata", on_delete=models.CASCADE
    )
    schema_version = models.CharField(max_length=8)


class TXCFileAttributes(models.Model):
    revision = models.ForeignKey(
        DatasetRevision, on_delete=models.CASCADE, related_name="txc_file_attributes"
    )
    schema_version = models.CharField(_("TransXChange Schema Version"), max_length=10)
    revision_number = models.IntegerField(_("File Revision Number"))
    modification = models.CharField(_("Modification"), max_length=28)
    creation_datetime = models.DateTimeField(_("File Creation Datetime"))
    modification_datetime = models.DateTimeField(_("File Modification Datetime"))
    filename = models.CharField(_("Filename"), max_length=512)
    service_code = models.CharField(_("Service Code"), max_length=100)
    national_operator_code = models.CharField(
        _("National Operator Code"), max_length=100
    )
    licence_number = models.CharField(_("Licence Number"), max_length=56, default="")
    operating_period_start_date = models.DateField(
        _("Operating Period Start Date"), null=True, blank=True
    )
    operating_period_end_date = models.DateField(
        _("Operating Period End Date"), null=True, blank=True
    )
    public_use = models.BooleanField(_("Is the service for public use"), default=True)
    line_names = ArrayField(
        models.CharField(_("Name of Lines"), max_length=255, blank=True),
        blank=True,
        default=list,
    )
    origin = models.CharField(_("Origin"), max_length=512, default="")
    destination = models.CharField(_("Destination"), max_length=512, default="")
    hash = models.CharField(_("Hash of file"), max_length=40, default="")

    objects = TXCFileAttributesQuerySet.as_manager()

    def __str__(self):
        return (
            f"revision_id={self.revision_id}, "
            f"schema_version={self.schema_version!r}, "
            f"revision_number={self.revision_number}, "
            f"modification={self.modification!r}, "
            f"creation_datetime={self.creation_datetime.isoformat()}, "
            f"modification_datetime={self.modification_datetime.isoformat()}, "
            f"filename={self.filename!r}, "
            f"service_code={self.service_code!r}, "
            f"origin={self.origin!r}, "
            f"destination={self.destination!r}, "
            f"national_operator_code={self.national_operator_code!r}, "
            f"hash={self.hash!r}"
        )

    @classmethod
    def from_txc_file(cls, txc_file: TXCFile, revision_id: int):
        return cls(
            revision_id=revision_id,
            schema_version=txc_file.header.schema_version,
            modification=txc_file.header.modification,
            revision_number=txc_file.header.revision_number,
            creation_datetime=txc_file.header.creation_datetime,
            modification_datetime=txc_file.header.modification_datetime,
            filename=txc_file.header.filename,
            national_operator_code=txc_file.operator.national_operator_code,
            licence_number=txc_file.operator.licence_number,
            service_code=txc_file.service.service_code,
            origin=txc_file.service.origin,
            destination=txc_file.service.destination,
            operating_period_start_date=txc_file.service.operating_period_start_date,
            operating_period_end_date=txc_file.service.operating_period_end_date,
            public_use=txc_file.service.public_use,
            line_names=[line.line_name for line in txc_file.service.lines],
            hash=txc_file.hash,
        )


class ConsumerStats(models.Model):
    organisation = models.OneToOneField(
        "Organisation",
        on_delete=models.CASCADE,
        help_text="Operator",
        null=False,
        blank=False,
        related_name="stats",
    )
    monthly_breakdown = models.FileField(
        _("Monthly breakdown per dataset per day"), default=None
    )
    weekly_unique_consumers = models.IntegerField(
        _("Number of unique consumers in the last 7 days"), default=0
    )
    weekly_downloads = models.IntegerField(
        _("Number of direct downloads in the last 7 days"), default=0
    )
    weekly_api_hits = models.IntegerField(
        _("Number of api hits in the last 7 days"), default=0
    )


class AVLComplianceCache(models.Model):
    dataset = models.OneToOneField(
        Dataset,
        on_delete=models.CASCADE,
        help_text="The data feed",
        related_name="avl_compliance_cached",
    )

    status = models.CharField(
        help_text="AVL compliance string",
        choices=COMPLIANCE_STATUS_CHOICES,
        blank=False,
        default=UNDERGOING,
        max_length=50,
    )


class ServiceCodeExemption(TimeStampedModel):
    class Meta:
        unique_together = ("licence", "registration_code")

    licence = models.ForeignKey(
        "Licence",
        on_delete=models.CASCADE,
        help_text="Organisation licence",
        related_name="service_code_exemptions",
    )
    registration_code = models.IntegerField(
        blank=False,
        null=False,
        help_text="The part of the service code after the licence prefix",
    )
    justification = models.CharField(
        blank=True,
        max_length=140,
        help_text="Justification for exemption",
    )
    exempted_by = models.ForeignKey(
        User,
        related_name="service_code_exemptions",
        on_delete=models.PROTECT,
        help_text="The user that added this exemption",
    )

    objects = ServiceCodeExemptionManager()

    def __str__(self) -> str:
        return (
            f"licence_id={self.licence}, "
            f"registration_code={self.registration_code}, "
            f"justification='{self.justification}'"
        )


class SeasonalService(TimeStampedModel):
    licence = models.ForeignKey(
        "Licence",
        on_delete=models.CASCADE,
        help_text="Organisation licence",
        related_name="seasonal_services",
    )
    registration_code = models.IntegerField(
        blank=False,
        null=False,
        help_text="The part of the service code after the licence prefix",
    )

    start = models.DateField(_("First day of season"), blank=False, null=False)

    end = models.DateField(_("Last day of season"), blank=False, null=False)

    objects = SeasonalServiceManager()

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["licence", "registration_code"], name="unique_service"
            )
        ]

    def __str__(self) -> str:
        return (
            f"licence_id={self.licence}, "
            f"registration_code={self.registration_code}, "
            f"season={self.start:%d/%m/%Y} to {self.end:%d/%m/%Y}"
        )
