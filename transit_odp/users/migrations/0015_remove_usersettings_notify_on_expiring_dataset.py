# Generated by Django 2.2.13 on 2020-09-17 11:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0014_usersettings_notify_avl_unavailable"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="usersettings",
            name="notify_on_expiring_dataset",
        ),
    ]
