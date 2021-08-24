from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.http.response import FileResponse
from django_extensions.db.models import TimeStampedModel

from transit_odp.common.utils.repr import nice_repr

User = get_user_model()
CHAR_LEN = 512


OPERATIONAL_EXPORTS_NAME = "operationalexports.zip"


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

    def __str__(self):
        return f"id={self.id!r}, date={self.date!s}"

    class Meta:
        verbose_name_plural = "Operational stats"


class APIRequest(TimeStampedModel):
    requestor = models.ForeignKey(User, on_delete=models.CASCADE)
    path_info = models.CharField(max_length=CHAR_LEN)
    query_string = models.CharField(max_length=CHAR_LEN)

    def __str__(self):
        return nice_repr(self)


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


class OperationalMetricsArchive(TimeStampedModel):
    archive = models.FileField()

    def __str__(self):
        return (
            f"id={self.id}, filename={self.archive.name!r}, "
            f"modified={self.modified.isoformat()}"
        )

    def to_http_response(self) -> Optional[FileResponse]:
        self.archive.seek(0)
        response = FileResponse(self.archive.open("rb"), as_attachment=True)
        response[
            "Content-Disposition"
        ] = f"attachment; filename={OPERATIONAL_EXPORTS_NAME}"
        return response
