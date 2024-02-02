# Generated by Django 2.2.6 on 2019-11-11 16:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transmodel", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TimingPattern",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "service_pattern",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="timing_patterns",
                        to="transmodel.ServicePattern",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TimingPatternStop",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "arrival",
                    models.DurationField(
                        help_text="The duration of time from the Vehicle Journey start time to reach service_pattern_stop"
                    ),
                ),
                (
                    "departure",
                    models.DurationField(
                        help_text="The duration of time from the Vehicle Journey start time to depart service_pattern_stop"
                    ),
                ),
                ("pickup_allowed", models.BooleanField()),
                ("setdown_allowed", models.BooleanField()),
                ("timing_point", models.BooleanField()),
                (
                    "service_pattern_stop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="timings",
                        to="transmodel.ServicePatternStop",
                    ),
                ),
                (
                    "timing_pattern",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="timing_pattern_stops",
                        to="transmodel.TimingPattern",
                    ),
                ),
            ],
        ),
    ]
