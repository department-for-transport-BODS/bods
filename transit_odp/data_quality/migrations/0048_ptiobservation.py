# Generated by Django 2.2.19 on 2021-03-15 12:08

import django.db.models.deletion
import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organisation", "0038_datasetrevision_num_of_timing_points"),
        ("data_quality", "0047_linemissingblockidwarning"),
    ]

    operations = [
        migrations.CreateModel(
            name="PTIObservation",
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
                    "filename",
                    models.CharField(
                        help_text="The name of the file the observation occurs in.",
                        max_length=256,
                    ),
                ),
                (
                    "line",
                    models.IntegerField(
                        help_text="The line number of the observation."
                    ),
                ),
                (
                    "details",
                    models.CharField(
                        help_text="Details of the observation.", max_length=1024
                    ),
                ),
                (
                    "element",
                    models.CharField(
                        help_text="The element which generated the observation.",
                        max_length=256,
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        help_text="The category of the observation.", max_length=1024
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True,
                        verbose_name="DateTime observation was created.",
                    ),
                ),
                (
                    "revision",
                    models.ForeignKey(
                        help_text="The revision that observation occurred in.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="organisation.DatasetRevision",
                    ),
                ),
            ],
        ),
    ]
