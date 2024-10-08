# Generated by Django 4.2.9 on 2024-08-21 10:59

from django.db import migrations
from transit_odp.dqs.constants import Checks, Level, Category
from django.conf import settings

AWS_ENVIRONMENT = settings.AWS_ENVIRONMENT.lower()


class Migration(migrations.Migration):

    dependencies = [
        ("dqs", "0005_create_dqs_checks"),
    ]
    queue_name = f"dqs-{AWS_ENVIRONMENT}-missing-journey-code-queue"

    operations = [
        migrations.RunSQL(
            "INSERT INTO dqs_checks(observation, importance, category, queue_name) VALUES ('"
            + Checks.MissingJourneyCode.value
            + "', '"
            + Level.critical.value
            + "', '"
            + Category.journey.value
            + "', '"
            + queue_name
            + "')"
        )
    ]
