# Generated by Django 3.1.13 on 2021-11-09 18:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("organisation", "0046_added_licence_model"),
    ]

    operations = [
        migrations.CreateModel(
            name="StuckRevision",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("organisation.datasetrevision",),
        ),
    ]
