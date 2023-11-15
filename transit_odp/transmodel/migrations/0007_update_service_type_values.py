from django.db import migrations, models


def update_type_column(apps, schema_editor):
    # Get models for the tables you want to work with
    Service = apps.get_model("transmodel", "Service")

    # Perform your custom logic
    for service_instance in Service.objects.all():
        # Check if corresponding record exists in Service.service_patterns.through model
        if not service_instance.service_patterns.through.objects.filter(
            service_id=service_instance.id
        ).exists():
            # Update the 'type' column in the ServiceModel
            service_instance.type = "flexible"
            service_instance.save()


class Migration(migrations.Migration):

    dependencies = [
        ("transmodel", "0006_service_service_type"),
    ]

    operations = [
        migrations.RunPython(update_type_column),
    ]
