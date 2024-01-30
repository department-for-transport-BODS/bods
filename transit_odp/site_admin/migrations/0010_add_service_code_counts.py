# Generated by Django 3.1.13 on 2021-10-13 14:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("site_admin", "0009_added_operational_metrics_export_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="operationalstats",
            name="registered_service_code_count",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="operationalstats",
            name="unregistered_service_code_count",
            field=models.IntegerField(null=True),
        ),
    ]
