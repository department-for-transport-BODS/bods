# Generated by Django 2.2.13 on 2021-02-11 13:02

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_quality", "0044_auto_20210125_1837"),
    ]

    operations = [
        migrations.CreateModel(
            name="MissingNOCWarning",
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
            ],
            options={
                "abstract": False,
            },
        ),
    ]
