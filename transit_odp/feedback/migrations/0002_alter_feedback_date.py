# Generated by Django 3.2.13 on 2022-07-13 16:59

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("feedback", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="feedback",
            name="date",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]
