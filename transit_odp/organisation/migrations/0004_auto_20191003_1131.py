# Generated by Django 2.2.5 on 2019-10-03 10:31
import logging

from django.db import migrations, models
from django.db.models import Count

import transit_odp.common.validators


class Migration(migrations.Migration):

    dependencies = [("organisation", "0003_auto_20191002_1339")]

    operations = [
        migrations.AlterField(
            model_name="datasetrevision",
            name="name",
            field=models.CharField(
                max_length=255,
                unique=False,
                validators=[transit_odp.common.validators.validate_profanity],
                verbose_name="Feed name",
            ),
        )
    ]
