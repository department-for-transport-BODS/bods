# Generated by Django 4.2.9 on 2024-03-11 06:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transmodel", "0015_vehiclejourney_service_pattern_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="servicedorganisations",
            name="organisation_code",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
