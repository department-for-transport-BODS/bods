# Generated by Django 2.2.6 on 2019-10-24 12:54
import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def fill_org_short_name(apps, schema_editor):
    logger.info("Populating fill_org_short_name for Organisation model")
    Organisation = apps.get_model("organisation", "Organisation")

    for organisation in Organisation.objects.all():
        organisation.short_name = organisation.name
        organisation.save()

    logger.info(f"short_name's updated")


class Migration(migrations.Migration):
    dependencies = [("organisation", "0017_organisation_short_name")]

    operations = [
        migrations.RunPython(
            fill_org_short_name, migrations.RunPython.noop, elidable=True
        )
    ]
