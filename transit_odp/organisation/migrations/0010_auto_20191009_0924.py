# Generated by Django 2.2.5 on 2019-10-09 08:24
import logging

from django.db import migrations
from django.db.models import F, Q

logger = logging.getLogger(__name__)


def fill_published_at(apps, schema_editor):
    logger.info(
        "Populating published_at field of published dataset revisions using created timestamp"
    )
    DatasetRevision = apps.get_model("organisation", "DatasetRevision")

    # Get published revisions with missing published_at field
    qs = DatasetRevision.objects.filter(
        Q(is_published=True) & Q(published_at__isnull=True)
    )
    logger.info(f"Populating {len(qs)} dataset revisions")

    # Populate published_at using 'created' field. This is not strictly true but ensures revisions at published in the
    # same order that they were created.
    qs.update(published_at=F("created"))
    logger.info(f"Dataset revisions updated")


class Migration(migrations.Migration):
    dependencies = [("organisation", "0009_datasetrevision_published_at")]

    operations = [
        migrations.RunPython(
            fill_published_at, migrations.RunPython.noop, elidable=True
        )
    ]
