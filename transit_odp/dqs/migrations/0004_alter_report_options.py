# Generated by Django 4.2.9 on 2024-08-07 10:51

from django.db import migrations
from transit_odp.dqs.constants import Checks, Level, Category
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("dqs", "0003_alter_observationresults_service_pattern_stop_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            "INSERT INTO dqs_checks(observation, importance, category, queue_name) VALUES ('"
            + Checks.NoTimingPointMoreThan15Mins.value
            + "', '"
            + Level.advisory.value
            + "', '"
            + Category.timing.value
            + "', 'dqs-local-no-timing-point-more-than-15-mins')"
        )
    ]
