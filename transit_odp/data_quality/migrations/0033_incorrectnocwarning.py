# Generated by Django 2.2.7 on 2019-12-03 16:55

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_quality", "0032_merge_20191203_1415"),
    ]

    operations = [
        migrations.CreateModel(
            name="IncorrectNOCWarning",
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
                ("noc", models.TextField()),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data_quality.DataQualityReport",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
