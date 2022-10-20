import logging

from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField
from django_extensions.db.models import TimeStampedModel

from transit_odp.common.enums import FeedErrorCategory, FeedErrorSeverity
from transit_odp.common.loggers import PipelineAdapter
from transit_odp.common.utils import sha1sum
from transit_odp.data_quality.models import DataQualityReport
from transit_odp.organisation.constants import DatasetType, TravelineRegions
from transit_odp.organisation.models import DatasetRevision
from transit_odp.organisation.notifications import (
    send_endpoint_validation_error_notification,
)
from transit_odp.pipelines import managers
from transit_odp.pipelines.constants import SchemaCategory
from transit_odp.pipelines.exceptions import PipelineException

logger = logging.getLogger(__name__)


# TODO - remove this model
# This model is hardly used yet it is used in the notification code to give
# the reason a dataset etl job has entered an error state.
# Need to rethink this
class DatasetETLError(TimeStampedModel):
    revision = models.ForeignKey(
        DatasetRevision, related_name="errors", on_delete=models.CASCADE, null=True
    )

    SEVERITY_CHOICES = [(e.value, e.name.capitalize()) for e in FeedErrorSeverity]
    severity = models.CharField(_("Severity"), choices=SEVERITY_CHOICES, max_length=255)

    CATEGORY_CHOICES = [(cat.value, cat.name.capitalize()) for cat in FeedErrorCategory]
    category = models.CharField(_("Category"), choices=CATEGORY_CHOICES, max_length=255)

    description = models.CharField(max_length=8096)


class TaskResult(TimeStampedModel):
    """A mixin that provides similar fields to django_celery_results' model for
    storing the status of a task/workflow.

    We're not using django_celery_results because:
      * we don't want to use Django as a backend for all Celery tasks, e.g.
      frequent 'monitoring' tasks
      * we want to model a task inheritance hierarchy in order to create subtypes of
      tasks with relationships to other models and other data such as progress
      and specific error_codes.
    """

    #: Task state is unknown (assumed pending since you know the id).
    PENDING = "PENDING"
    #: Task was received by a worker (only used in events).
    RECEIVED = "RECEIVED"
    #: Task was started by a worker (:setting:`task_track_started`).
    STARTED = "STARTED"
    #: Task succeeded
    SUCCESS = "SUCCESS"
    #: Task failed
    FAILURE = "FAILURE"

    ALL_STATES = frozenset({PENDING, RECEIVED, STARTED, SUCCESS, FAILURE})
    TASK_STATE_CHOICES = sorted(zip(ALL_STATES, ALL_STATES))

    task_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name=_("Task ID"),
        help_text=_("The ID for the Task that was run"),
    )
    status = models.CharField(
        max_length=50,
        default=PENDING,
        db_index=True,
        choices=TASK_STATE_CHOICES,
        verbose_name=_("Task State"),
        help_text=_("Current state of the task being run"),
    )
    completed = models.DateTimeField(
        db_index=True,
        blank=True,
        null=True,
        verbose_name=_("Completed DateTime"),
        help_text=_("Datetime field when the task was completed in UTC"),
    )

    class Meta(TimeStampedModel.Meta):
        abstract = True

    def to_success(self):
        self.status = self.SUCCESS
        self.completed = now()

    def to_error(self):
        self.status = self.FAILURE
        self.completed = now()


class DatasetETLTaskResult(TaskResult):

    revision = models.ForeignKey(
        DatasetRevision, related_name="etl_results", on_delete=models.CASCADE
    )
    progress = models.IntegerField(_("Progress"), default=0)

    # Store data about how the task failed

    # These error codes indicate an error on behalf of the user
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    ZIP_TOO_LARGE = "ZIP_TOO_LARGE"
    NESTED_ZIP_FORBIDDEN = "NESTED_ZIP_FORBIDDEN"
    NO_DATA_FOUND = "NO_DATA_FOUND"
    XML_SYNTAX_ERROR = "XML_SYNTAX_ERROR"
    DANGEROUS_XML_ERROR = "DANGEROUS_XML_ERROR"
    SCHEMA_VERSION_MISSING = "SCHEMA_VERSION_MISSING"
    SCHEMA_VERSION_NOT_SUPPORTED = "SCHEMA_VERSION_NOT_SUPPORTED"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    DATASET_EXPIRED = "DATASET_EXPIRED"
    SUSPICIOUS_FILE = "SUSPICIOUS_FILE"

    # This error code indicates an error that is likely not the user's fault
    SYSTEM_ERROR = "SYSTEM_ERROR"

    ALL_ERROR_CODES = frozenset(
        {
            SYSTEM_ERROR,
            FILE_TOO_LARGE,
            ZIP_TOO_LARGE,
            NESTED_ZIP_FORBIDDEN,
            NO_DATA_FOUND,
            XML_SYNTAX_ERROR,
            DANGEROUS_XML_ERROR,
            SCHEMA_VERSION_MISSING,
            SCHEMA_VERSION_NOT_SUPPORTED,
            SCHEMA_ERROR,
            DATASET_EXPIRED,
            SUSPICIOUS_FILE,
        }
    )
    TASK_ERROR_CODE_CHOICES = sorted(zip(ALL_ERROR_CODES, ALL_ERROR_CODES))

    task_name_failed = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("The name of the Celery task which failed"),
    )
    error_code = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        choices=TASK_ERROR_CODE_CHOICES,
        verbose_name=_("Task Error Code"),
        help_text=_("The error code returned for the failed task"),
    )
    additional_info = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name=_("Additional Information"),
        help_text=_("Additional information about a failed task"),
    )

    def to_success(self):
        super().to_success()
        self.task_name_failed = ""
        self.error_code = ""

    @transaction.atomic()
    def to_error(self, task_name, error_code):
        if self.status != self.FAILURE:
            super().to_error()
            self.task_name_failed = task_name
            self.error_code = error_code

            # TODO - remove. The revision shouldn't contain task state
            self.revision.to_error()
            self.revision.save()

            # TODO - this is probably too tightly coupled

            if task_name == "dataset_validate":
                # Currently the only error template we have is when the validation
                # fails. This may need to be redone if we expand notifying on errors
                send_endpoint_validation_error_notification(self.revision.dataset)

            self.save()

    def handle_general_pipeline_exception(
        self,
        exception: Exception,
        adapter: PipelineAdapter,
        message: str = None,
        task_name="dataset_validate",
    ):
        message = message or str(exception)
        adapter.error(message, exc_info=True)
        self.to_error(task_name, DatasetETLTaskResult.SYSTEM_ERROR)
        self.additional_info = message
        self.save()
        raise PipelineException(message) from exception

    def update_progress(self, progress: int):
        self.progress = progress
        self.save()


class DataQualityTask(TaskResult):
    """DataQualityTask is a remote proxy for the task running on the
    Data Quality Service (DQS)."""

    revision = models.ForeignKey(
        DatasetRevision, related_name="data_quality_tasks", on_delete=models.CASCADE
    )
    report = models.OneToOneField(
        DataQualityReport,
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        help_text="The DQS report returned by DQS when the task has finished",
    )
    task_id = models.UUIDField(
        null=True,
        unique=True,
        help_text=(
            "The task_id returned by DQS when the task has been "
            "successfully received"
        ),
    )
    message = models.TextField(
        default="", help_text="Contains more details about the DQS job"
    )

    objects = managers.DataQualityTaskManager()

    def __str__(self):
        return f"DataQualityTask(id={self.id!r}, task_id={self.task_id!r})"

    def success(self, message: str):
        logger.info(f"{self} is done")
        if self.status != self.SUCCESS:
            self.status = self.SUCCESS
            self.message = message

    def failure(self, message: str):
        logger.info(f"{self} has failed with reason: {message}")
        if self.status != self.FAILURE:
            self.status = self.FAILURE
            self.message = message

    def started(self, message: str):
        logger.info(f"{self} is in-progress. Current message: {message}")
        # The current Celery task scheduling logic doesn't prevent two monitoring
        # tasks running simultaneously
        # This prevents the task being updated by a late arriving payload back
        # into the started state
        if self.status != self.SUCCESS and self.status != self.FAILURE:
            self.status = self.STARTED
            self.message = message


class RemoteDatasetHealthCheckCount(models.Model):
    revision = models.OneToOneField(
        "organisation.DatasetRevision",
        related_name="availability_retry_count",
        on_delete=models.CASCADE,
    )
    modified = models.DateTimeField(auto_now=True)
    count = models.PositiveIntegerField(default=0)

    def reset(self):
        """Resets availability retry counter"""
        if self.count > 0:
            self.count = 0
            self.save()


class BulkDataArchive(models.Model):
    created = CreationDateTimeField(_("created"))
    data = models.FileField(help_text=_("A zip file containing all active datasets"))
    dataset_type = models.IntegerField(
        choices=DatasetType.choices(), default=DatasetType.TIMETABLE
    )
    compliant_archive = models.BooleanField(
        _("Whether all the datasets are compliant."), default=False
    )
    traveline_regions = models.CharField(
        _("TravelineRegion"),
        max_length=4,
        choices=TravelineRegions.choices,
        default=TravelineRegions.ALL.value,
    )

    class Meta:
        get_latest_by = "-created"
        ordering = ("-created",)

    def __str__(self):
        return f"BulkDataArchive(created={self.created}, data='{self.data.name}')"


class ChangeDataArchive(models.Model):
    published_at = models.DateField(
        _("published_at"), help_text="The date of publication"
    )
    data = models.FileField(
        help_text=_("A zip file containing all datasets published at 'published_at'")
    )

    class Meta:
        get_latest_by = "-published_at"
        ordering = ("-published_at",)

    def __str__(self):
        return (
            f"ChangeDataArchive(published_at={self.published_at}, "
            f"data={self.data.name!r})"
        )


class SchemaDefinition(TimeStampedModel):
    category = models.CharField(
        null=False, unique=True, max_length=6, choices=SchemaCategory.choices
    )
    checksum = models.CharField(null=False, max_length=40)
    schema = models.FileField(null=False, validators=[FileExtensionValidator([".zip"])])

    @transaction.atomic
    def update_definition(self, content: bytes, name: str):
        """
        Replaces schema zip with new content. Note this will delete the file in the
        file manager

        Args:
            content: zip file in bytes to be saved
            name: filename of new zip file
        """
        self.schema.delete()
        self.schema = ContentFile(content, name)
        self.checksum = sha1sum(content)
        self.save()
