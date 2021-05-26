# Generated by Django 2.2.19 on 2021-04-20 15:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organisation", "0038_datasetrevision_num_of_timing_points"),
    ]

    operations = [
        migrations.CreateModel(
            name="TXCFileAttributes",
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
                ("schema_version", models.CharField(max_length=10)),
                ("revision_number", models.IntegerField()),
                ("creation_datetime", models.DateTimeField()),
                ("modificaton_datetime", models.DateTimeField()),
                ("filename", models.CharField(max_length=512)),
                ("service_code", models.CharField(max_length=100)),
                (
                    "revision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="txc_file_attributes",
                        to="organisation.DatasetRevision",
                    ),
                ),
            ],
        ),
    ]
