from django.db import migrations


from transit_odp.transmodel.models import StopActivity


def insert_data(apps, schema_editor):

    data_dict = {
        "pickUp": {"is_pickup": True, "is_setdown": False, "is_driverrequest": False},
        "setDown": {"is_pickup": False, "is_setdown": True, "is_driverrequest": False},
        "pickUpAndSetDown": {
            "is_pickup": True,
            "is_setdown": True,
            "is_driverrequest": False,
        },
        "none": {"is_pickup": True, "is_setdown": True, "is_driverrequest": False},
        "pass": {"is_pickup": False, "is_setdown": False, "is_driverrequest": False},
        "pickUpDriverRequest": {
            "is_pickup": True,
            "is_setdown": False,
            "is_driverrequest": True,
        },
        "setDownDriverRequest": {
            "is_pickup": False,
            "is_setdown": True,
            "is_driverrequest": True,
        },
        "pickUpAndSetDownDriverRequest": {
            "is_pickup": True,
            "is_setdown": True,
            "is_driverrequest": True,
        },
    }

    for name, values in data_dict.items():
        StopActivity.objects.create(
            is_pickup=values["is_pickup"],
            is_setdown=values["is_setdown"],
            is_driverrequest=values["is_driverrequest"],
            name=name,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("transmodel", "0025_remove_servicedorganisationworkingdays_serviced_organisation_and_more"),
    ]

    operations = [
        migrations.RunPython(insert_data),
    ]
