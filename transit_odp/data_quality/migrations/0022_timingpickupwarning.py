# Generated by Django 2.2.7 on 2019-11-29 10:21

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_quality", "0021_servicepatternservicelink"),
    ]

    operations = [
        migrations.CreateModel(
            name="TimingPickUpWarning",
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
                    "service_links",
                    models.ManyToManyField(to="data_quality.ServiceLink"),
                ),
                (
                    "timing_pattern",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data_quality.TimingPattern",
                    ),
                ),
                (
                    "timings",
                    models.ManyToManyField(to="data_quality.TimingPatternStop"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
