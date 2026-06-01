import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import connection, models, transaction
from django.db.models import F, Q, UniqueConstraint
from django.http import HttpRequest
from django.http.response import FileResponse
from django_extensions.db.models import TimeStampedModel

from transit_odp.common.utils.repr import nice_repr
from transit_odp.site_admin.constants import ARCHIVE_CATEGORY_FILENAME, ArchiveCategory
from transit_odp.site_admin.querysets import (
    APIRequestQuerySet,
    ResourceRequestCounterQuerySet,
)

User = get_user_model()
CHAR_LEN = 512
logger = logging.getLogger(__name__)


class OperationalStats(models.Model):
    date = models.DateField(unique=True)

    #  operator and user counts
    operator_count = models.IntegerField()
    operator_user_count = models.IntegerField()
    agent_user_count = models.IntegerField()
    consumer_count = models.IntegerField()

    # active dataset counts
    timetables_count = models.IntegerField()
    avl_count = models.IntegerField()
    fares_count = models.IntegerField()

    # number of operators with at least one published dataset
    published_timetable_operator_count = models.IntegerField()
    published_avl_operator_count = models.IntegerField()
    published_fares_operator_count = models.IntegerField()

    # vehicles
    vehicle_count = models.IntegerField(default=0)

    # services
    registered_service_code_count = models.IntegerField(null=True)
    unregistered_service_code_count = models.IntegerField(null=True)

    def __str__(self):
        return f"id={self.id!r}, date={self.date!s}"

    class Meta:
        verbose_name_plural = "Operational stats"


class APIRequest(TimeStampedModel):
    requestor = models.ForeignKey(User, on_delete=models.CASCADE)
    path_info = models.CharField(max_length=CHAR_LEN)
    query_string = models.CharField(max_length=CHAR_LEN)

    objects = models.Manager.from_queryset(APIRequestQuerySet)()

    class Meta:
        indexes = [models.Index(fields=["created"], name="apirequest_created_idx")]

    def __str__(self):
        return nice_repr(self)


class ResourceRequestCounter(models.Model):
    date = models.DateField()
    requestor = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    path_info = models.CharField(max_length=CHAR_LEN)
    counter = models.IntegerField(null=False, default=0)

    objects = models.Manager.from_queryset(ResourceRequestCounterQuerySet)()

    class Meta:
        indexes = [models.Index(fields=["date"], name="requestcounter_date_idx")]
        # have to do this over 2 constraints because unique constraints do not work
        # for nullable fields
        constraints = [
            UniqueConstraint(
                fields=["date", "requestor_id", "path_info"],
                name="requestcounter_unique_with_requestor",
            ),
            UniqueConstraint(
                fields=["date", "path_info"],
                condition=Q(requestor_id=None),
                name="requestcounter_unique_without_requestor",
            ),
        ]

    def __str__(self):
        return nice_repr(self)

    @classmethod
    def _upsert_counter_for_request_key(
        cls, *, day, requestor_id: Optional[int], path_info: str
    ) -> None:
        if connection.vendor != "postgresql":
            resource_counter, _ = cls.objects.get_or_create(
                requestor_id=requestor_id,
                path_info=path_info,
                date=day,
                defaults={"counter": 0},
            )
            cls.objects.filter(id=resource_counter.id).update(counter=F("counter") + 1)
            return

        table = connection.ops.quote_name(cls._meta.db_table)
        if requestor_id is None:
            query = f"""
                INSERT INTO {table} (date, requestor_id, path_info, counter)
                VALUES (%s, %s, %s, 1)
                ON CONFLICT (date, path_info) WHERE requestor_id IS NULL
                DO UPDATE SET counter = {table}.counter + 1
            """
        else:
            query = f"""
                INSERT INTO {table} (date, requestor_id, path_info, counter)
                VALUES (%s, %s, %s, 1)
                ON CONFLICT (date, requestor_id, path_info)
                DO UPDATE SET counter = {table}.counter + 1
            """
        with connection.cursor() as cursor:
            cursor.execute(query, [day, requestor_id, path_info])

    @classmethod
    def from_request(cls, request: HttpRequest):
        requestor_id = request.user.id if request.user.is_authenticated else None
        path_info = request.path
        day = datetime.now().date()

        def write_counter_after_response_commit():
            try:
                cls._upsert_counter_for_request_key(
                    day=day, requestor_id=requestor_id, path_info=path_info
                )
            except Exception:
                logger.exception(
                    "Failed to increment resource request counter", extra={"path": path_info}
                )

        transaction.on_commit(write_counter_after_response_commit)


class MetricsArchive(models.Model):
    start = models.DateField()
    end = models.DateField()
    archive = models.FileField()

    def __str__(self):
        return f"{self.start:%Y-%m-%d}, {self.end:%Y-%m-%d}"

    def to_http_response(self) -> Optional[FileResponse]:
        zip_filename = (
            f"consumer_api_metrics_{self.start:%Y_%m_%d}_{self.end:%Y_%m_%d}.zip"
        )
        self.archive.seek(0)
        response = FileResponse(self.archive.open("rb"), as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={zip_filename}"
        return response


class DocumentArchive(TimeStampedModel):
    archive = models.FileField()
    category = models.CharField(
        choices=ArchiveCategory.choices,
        default=ArchiveCategory.OPERATIONAL_METRICS.value,
        max_length=50,
    )

    def __str__(self):
        return (
            f"id={self.id}, category={self.category}, filename={self.filename!r}, "
            f"modified={self.modified.isoformat()}"
        )

    @property
    def filename(self):
        path = Path(self.archive.name)
        return path.name

    def to_http_response(self) -> Optional[FileResponse]:
        filename = ARCHIVE_CATEGORY_FILENAME[self.category]
        self.archive.seek(0)
        response = FileResponse(self.archive.open("rb"), as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
