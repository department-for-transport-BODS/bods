from django.db import migrations


from transit_odp.transmodel.models import StopActivity


def insert_data(apps, schema_editor):

    StopActivity.objects.create(
        is_pickup=False,
        is_setdown=False,
        is_driverrequest=False,
        name="noPickUpAndSetDown",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("transmodel", "0043_servicepatterndistance_coord_track_distance_and_more"),
    ]

    operations = [
        migrations.RunPython(insert_data),
    ]
