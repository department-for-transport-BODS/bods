# Generated by Django 4.2.9 on 2024-05-07 16:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("transmodel", "0027_auto_create_stop_activity_records"),
    ]

    operations = [
        migrations.AlterField(
            model_name="servicepatternstop",
            name="stop_activity",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="stop_activity",
                to="transmodel.stopactivity",
            ),
        ),
        migrations.AlterField(
            model_name="vehiclejourney",
            name="block_number",
            field=models.CharField(default=None, max_length=10, null=True),
        ),
    ]
