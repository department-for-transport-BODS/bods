# Generated by Django 4.2.9 on 2024-06-26 10:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("organisation", "0060_organisation_is_abods_global_viewer"),
    ]

    operations = [
        migrations.CreateModel(
            name="FaresStuckRevision",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("organisation.datasetrevision",),
        ),
    ]
