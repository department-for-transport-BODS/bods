# Generated by Django 2.2.13 on 2021-01-25 18:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("data_quality", "0043_schemanottxc24warning_squashed_0044_auto_20210125_1552"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="incorrectnocwarning",
            unique_together={("report", "noc")},
        ),
    ]
