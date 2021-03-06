# Generated by Django 2.2.8 on 2019-12-03 15:14

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_quality", "0031_merge_20191203_0008"),
    ]

    operations = [
        migrations.CreateModel(
            name="StopIncorrectTypeWarning",
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
                ("stop_type", models.TextField()),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data_quality.DataQualityReport",
                    ),
                ),
                (
                    "stop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data_quality.StopPoint",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
