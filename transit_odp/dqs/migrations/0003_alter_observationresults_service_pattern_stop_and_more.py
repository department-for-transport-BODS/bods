# Generated by Django 4.2.9 on 2024-07-01 11:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("transmodel", "0028_alter_servicepatternstop_stop_activity_and_more"),
        ("dqs", "0002_custom_create_dqs_checks_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="observationresults",
            name="service_pattern_stop",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dqs_observationresult_service_pattern_stop",
                to="transmodel.servicepatternstop",
            ),
        ),
        migrations.AlterField(
            model_name="observationresults",
            name="vehicle_journey",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dqs_observationresult_vehicle_journey",
                to="transmodel.vehiclejourney",
            ),
        ),
    ]