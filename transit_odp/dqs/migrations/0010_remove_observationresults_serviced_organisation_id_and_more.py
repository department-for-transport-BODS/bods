# Generated by Django 4.2.14 on 2024-10-25 07:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dqs", "0009_observationresults_serviced_organisation_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="observationresults",
            name="serviced_organisation_vehicle_journey",
            field=models.ForeignKey(
                blank=True,
                default=None,
                help_text="Contains the link to serviced organisation id",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dqs_observationresult_serviced_organisation_vehicle_journey",
                to="transmodel.servicedorganisationvehiclejourney",
            ),
        )
    ]