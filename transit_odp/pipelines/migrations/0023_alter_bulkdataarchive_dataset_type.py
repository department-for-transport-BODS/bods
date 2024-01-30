# Generated by Django 3.2.20 on 2023-11-22 13:36

from django.db import migrations, models
import transit_odp.organisation.constants


class Migration(migrations.Migration):
    dependencies = [
        ("pipelines", "0022_alter_datasetetltaskresult_error_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bulkdataarchive",
            name="dataset_type",
            field=models.IntegerField(
                choices=[
                    (1, "TIMETABLE"),
                    (2, "AVL"),
                    (3, "FARES"),
                    (4, "DISRUPTIONS"),
                ],
                default=transit_odp.organisation.constants.DatasetType["TIMETABLE"],
            ),
        ),
    ]
