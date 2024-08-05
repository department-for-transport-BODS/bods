from django.db import migrations


def update_statuses_forward(apps, schema_editor):
    """Update AVL feed statuses to new values"""
    dataset = apps.get_model("organisation", "dataset")

    old_to_new_status_map = {
        "DEPLOYING": "live",
        "SYSTEM_ERROR": "error",
        "FEED_UP": "live",
        "FEED_DOWN": "inactive",
    }

    for row in dataset.objects.all():
        row.avl_feed_status = old_to_new_status_map[row.avl_feed_status]
        row.save()


def update_statuses_backward(apps, schema_editor):
    """Update AVL feed statuses to old values"""
    dataset = apps.get_model("organisation", "dataset")

    new_to_old_status_map = {
        "live": "FEED_UP",
        "inactive": "FEED_DOWN",
        "error": "SYSTEM_ERROR",
    }

    for row in dataset.objects.all():
        row.avl_feed_status = new_to_old_status_map[row.avl_feed_status]
        row.save()


class Migration(migrations.Migration):

    dependencies = [("organisation", "0063_alter_organisation_admin_areas")]

    operations = [
        migrations.RunPython(update_statuses_forward, update_statuses_backward)
    ]
