# Generated by Django 2.2.9 on 2020-02-11 14:01
import logging

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

logger = logging.getLogger(__name__)


def fill_contact(apps, schema_editor):
    logger.info("Populating contact field in dataset with user")
    Dataset = apps.get_model("organisation", "Dataset")
    Revision = apps.get_model("organisation", "DatasetRevision")

    for dataset in Dataset.objects.all():
        created_user = None
        try:
            # First attempt is to get the original modified user
            useful_revision = dataset.revisions.exclude(
                last_modified_user=None
            ).earliest("id")
            created_user = useful_revision.last_modified_user
        except Revision.DoesNotExist:
            pass

        if created_user is None:
            try:
                # Second attempt is to get the original publisher
                useful_revision = dataset.revisions.exclude(published_by=None).earliest(
                    "id"
                )
                created_user = useful_revision.published_by
            except Revision.DoesNotExist:
                pass

        if created_user is None:
            # This must be in a really confused state just use organisation key contact
            created_user = dataset.organisation.key_contact

        dataset.contact = created_user
        dataset.save()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisation", "0026_organisation_is_active"),
        ("site_admin", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="contact",
            field=models.ForeignKey(
                blank=True,
                help_text="This user will receive all notifications",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="created_datasets",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(fill_contact, migrations.RunPython.noop, elidable=True),
    ]
