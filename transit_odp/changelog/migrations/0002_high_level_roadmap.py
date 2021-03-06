# Generated by Django 3.0.14 on 2021-09-02 13:49

import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("changelog", "0001_known_issues"),
    ]

    operations = [
        migrations.CreateModel(
            name="HighLevelRoadMap",
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
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                ("description", models.TextField(verbose_name="Description")),
            ],
            options={
                "verbose_name": "High Level Road Map",
                "verbose_name_plural": "High Level Road Map",
            },
        ),
    ]
