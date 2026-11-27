from django.db import migrations


def insert_data(apps, schema_editor):
    stop_activity = apps.get_model("transmodel", "StopActivity")
    stop_activity.objects.get_or_create(
        name="noPickUpAndSetDown",
        defaults={
            "is_pickup": False,
            "is_setdown": False,
            "is_driverrequest": False,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("transmodel", "0043_servicepatterndistance_coord_track_distance_and_more"),
    ]

    operations = [
        migrations.RunPython(insert_data),
    ]
