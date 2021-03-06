# Generated by Django 2.2.13 on 2021-02-18 13:37

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_quality", "0045_missingnocwarning"),
    ]

    operations = [
        migrations.CreateModel(
            name="LineExpiredWarning",
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
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data_quality.DataQualityReport",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data_quality.Service",
                    ),
                ),
                (
                    "vehicle_journeys",
                    models.ManyToManyField(to="data_quality.VehicleJourney"),
                ),
            ],
            options={
                "unique_together": {("report", "service")},
            },
        ),
    ]
