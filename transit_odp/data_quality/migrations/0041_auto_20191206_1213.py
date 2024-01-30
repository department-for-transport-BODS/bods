# Generated by Django 2.2.8 on 2019-12-06 12:13

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data_quality", "0040_merge_20191205_1737"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="firststopsetdownonlywarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="firststopsetdownonlywarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="firststopsetdownonlywarning",
            name="timings",
        ),
        migrations.RemoveField(
            model_name="journeyoverlapwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="journeyoverlapwarning",
            name="stops",
        ),
        migrations.RemoveField(
            model_name="journeyoverlapwarning",
            name="vehicle_journey",
        ),
        migrations.RemoveField(
            model_name="laststopnottimingwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="laststopnottimingwarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="laststoppickuponlywarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="laststoppickuponlywarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="laststoppickuponlywarning",
            name="timings",
        ),
        migrations.RemoveField(
            model_name="multiplestopswarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="multiplestopswarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="multiplestopswarning",
            name="timings",
        ),
        migrations.DeleteModel(
            name="FirstStopNotTimingWarning",
        ),
        migrations.DeleteModel(
            name="FirstStopSetDownOnlyWarning",
        ),
        migrations.DeleteModel(
            name="JourneyOverlapWarning",
        ),
        migrations.DeleteModel(
            name="LastStopNotTimingWarning",
        ),
        migrations.DeleteModel(
            name="LastStopPickUpOnlyWarning",
        ),
        migrations.DeleteModel(
            name="MultipleStopsWarning",
        ),
    ]
