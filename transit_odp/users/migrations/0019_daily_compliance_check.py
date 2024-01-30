# Generated by Django 3.0.14 on 2021-09-07 11:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0018_added_notes_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersettings",
            name="daily_compliance_check_alert",
            field=models.BooleanField(
                default=True, verbose_name="Daily SIRI-VM compliance check alert"
            ),
        ),
    ]
