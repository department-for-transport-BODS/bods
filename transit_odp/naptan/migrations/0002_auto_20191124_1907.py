# Generated by Django 2.2.7 on 2019-11-24 19:07

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("naptan", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="adminarea",
            name="date_of_issue",
        ),
        migrations.RemoveField(
            model_name="adminarea",
            name="issue_version",
        ),
        migrations.RemoveField(
            model_name="district",
            name="date_of_issue",
        ),
        migrations.RemoveField(
            model_name="district",
            name="issue_version",
        ),
        migrations.RemoveField(
            model_name="locality",
            name="date_of_issue",
        ),
        migrations.RemoveField(
            model_name="locality",
            name="issue_version",
        ),
        migrations.RemoveField(
            model_name="locality",
            name="last_change",
        ),
    ]
