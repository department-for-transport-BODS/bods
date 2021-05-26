# Generated by Django 2.2.6 on 2019-11-11 17:49

import uuid

import django.core.validators
import django.db.models.deletion
import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("organisation", "0019_auto_20191024_1431"),
        ("transmodel", "0003_vehiclejourney"),
        ("naptan", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DataQualityReport",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to="",
                        validators=[
                            django.core.validators.FileExtensionValidator([".json"])
                        ],
                    ),
                ),
                (
                    "revision",
                    models.ForeignKey(
                        help_text="Data quality report",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="report",
                        to="organisation.DatasetRevision",
                    ),
                ),
            ],
            options={
                "ordering": ("-created",),
                "get_latest_by": "created",
            },
        ),
        migrations.CreateModel(
            name="ServiceLinkMissingStopWarning",
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
                    "service_link",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transmodel.ServiceLink",
                    ),
                ),
                (
                    "stops",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="naptan.StopPoint",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="JourneyOverlapWarning",
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
                    "stops",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="naptan.StopPoint",
                    ),
                ),
                (
                    "vehicle_journey",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transmodel.VehicleJourney",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="JourneyDuplicateWarning",
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
                    "vehicle_journey",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transmodel.VehicleJourney",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
