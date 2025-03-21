# Generated by Django 4.2.14 on 2025-02-10 13:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("transmodel", "0035_alter_service_service_code"),
        ("organisation", "0069_consumerfeedback_is_suppressed_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="consumerfeedback",
            name="service_pattern",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="feedback_service_pattern",
                to="transmodel.servicepattern",
            ),
        ),
        migrations.AlterField(
            model_name="consumerfeedback",
            name="is_suppressed",
            field=models.BooleanField(
                blank=True,
                default=None,
                help_text="Contains whether the observation result is suppressed",
                null=True,
            ),
        ),
    ]
