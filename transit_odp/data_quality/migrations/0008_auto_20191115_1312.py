# Generated by Django 2.2.7 on 2019-11-15 13:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_quality", "0007_auto_20191114_1744"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="servicepattern",
            name="services",
        ),
        migrations.AddField(
            model_name="servicepattern",
            name="service",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="service_patterns",
                to="data_quality.Service",
            ),
            preserve_default=False,
        ),
    ]
