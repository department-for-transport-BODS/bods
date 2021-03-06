# Generated by Django 2.2.13 on 2020-07-13 11:57

from django.db import migrations, models

import transit_odp.organisation.constants


class Migration(migrations.Migration):

    dependencies = [
        ("pipelines", "0015_auto_20200408_2152"),
    ]

    operations = [
        migrations.AddField(
            model_name="bulkdataarchive",
            name="dataset_type",
            field=models.IntegerField(
                choices=[(1, "TIMETABLE"), (2, "AVL"), (3, "FARES")],
                default=transit_odp.organisation.constants.DatasetType(1),
            ),
        ),
    ]
