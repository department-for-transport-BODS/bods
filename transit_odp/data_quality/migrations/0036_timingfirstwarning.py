# Generated by Django 2.2.8 on 2019-12-04 17:03

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_quality", "0035_merge_20191204_1332"),
    ]

    operations = [
        migrations.CreateModel(
            name="TimingFirstWarning",
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
