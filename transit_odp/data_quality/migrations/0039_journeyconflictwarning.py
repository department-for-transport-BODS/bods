# Generated by Django 2.2.8 on 2019-12-05 17:19

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_quality", "0038_merge_20191205_1012"),
    ]

    operations = [
        migrations.CreateModel(
            name="JourneyConflictWarning",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "conflict",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conflict",
                        to="data_quality.VehicleJourney",
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data_quality.DataQualityReport",
                    ),
                ),
                ("stops", models.ManyToManyField(to="data_quality.StopPoint")),
                (
                    "vehicle_journey",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data_quality.VehicleJourney",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
