# Generated by Django 4.2.14 on 2024-11-21 03:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transmodel", "0031_tracks_tracksvehiclejourney"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tracksvehiclejourney",
            name="sequence_number",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddConstraint(
            model_name="tracks",
            constraint=models.UniqueConstraint(
                fields=("from_atco_code", "to_atco_code"),
                name="unique_from_to_atco_code",
            ),
        ),
    ]
