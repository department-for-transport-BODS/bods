# Generated by Django 3.1.14 on 2022-02-01 17:13
from logging import getLogger

from django.conf import settings
from django.db import migrations

from transit_odp.organisation.constants import EXPIRED, INACTIVE
from transit_odp.organisation.models import DatasetRevision as DR
from transit_odp.organisation.querysets import DatasetRevisionQuerySet
from transit_odp.organisation.updaters import DEACTIVATE_COMMENT
from transit_odp.pipelines.models import RemoteDatasetHealthCheckCount as HCC

logger = getLogger(__name__)


def convert_expired_to_inactive(apps, schema_editor):
    RemoteDatasetHealthCheckCount: HCC = apps.get_model(
        "pipelines", "RemoteDatasetHealthCheckCount"
    )
    DatasetRevision: DR = apps.get_model("organisation", "DatasetRevision")

    unreachable_revisions = RemoteDatasetHealthCheckCount.objects.filter(
        count=settings.FEED_MONITOR_MAX_RETRY_ATTEMPTS
    ).values_list("revision_id", flat=True)
    revisions: DatasetRevisionQuerySet = DatasetRevision.objects.filter(
        id__in=unreachable_revisions, status=EXPIRED
    )
    logger.info(f"Converting {revisions.count()} expired revisions to inactive")

    revisions.update(status=INACTIVE, comment=DEACTIVATE_COMMENT)


def rollback_expired_to_inactive(apps, schema_editor):
    RemoteDatasetHealthCheckCount: HCC = apps.get_model(
        "pipelines", "RemoteDatasetHealthCheckCount"
    )
    DatasetRevision: DR = apps.get_model("organisation", "DatasetRevision")

    unreachable_revisions = RemoteDatasetHealthCheckCount.objects.filter(
        count=settings.FEED_MONITOR_MAX_RETRY_ATTEMPTS
    ).values_list("revision_id", flat=True)

    inactive_revisions = DatasetRevision.objects.filter(
        id__in=unreachable_revisions, status=INACTIVE
    )

    logger.info(f"Reverting {inactive_revisions.count()} back to expired")
    inactive_revisions.update(status=EXPIRED, comment="")


class Migration(migrations.Migration):

    dependencies = [
        ("organisation", "0049_added_origin_destination_to_file"),
        ("pipelines", "0020_added_traveline_region_field"),
    ]

    operations = [
        migrations.RunPython(convert_expired_to_inactive, rollback_expired_to_inactive)
    ]
