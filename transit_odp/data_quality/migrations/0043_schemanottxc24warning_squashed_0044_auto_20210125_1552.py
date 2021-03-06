# Generated by Django 2.2.13 on 2021-01-25 15:54

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("data_quality", "0043_schemanottxc24warning"),
        ("data_quality", "0044_auto_20210125_1552"),
    ]

    dependencies = [
        ("data_quality", "0042_merge_20191206_1427"),
    ]

    operations = [
        migrations.CreateModel(
            name="SchemaNotTXC24Warning",
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
                ("schema", models.TextField()),
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
                "unique_together": {("schema", "report")},
            },
        ),
    ]
