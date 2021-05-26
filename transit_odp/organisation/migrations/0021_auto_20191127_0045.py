# Generated by Django 2.2.7 on 2019-11-27 00:45

import django_fsm
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("organisation", "0020_remove_datasetrevision_line_names"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datasetrevision",
            name="status",
            field=django_fsm.FSMField(
                blank=True,
                choices=[
                    ("pending", "Pending"),
                    ("draft", "Draft"),
                    ("indexing", "Processing"),
                    ("live", "Published"),
                    ("success", "Draft"),
                    ("expiring", "Soon to expire"),
                    ("warning", "Warning"),
                    ("error", "Error"),
                    ("expired", "Expired"),
                    ("deleted", "Deleted"),
                ],
                default="pending",
                max_length=20,
                verbose_name="Status",
            ),
        ),
    ]
