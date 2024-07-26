# Generated by Django 4.2.9 on 2024-07-24 10:19

from django.db import migrations
import transit_odp.common.fields
import transit_odp.disruptions.storage


class Migration(migrations.Migration):

    dependencies = [
        ("disruptions", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="disruptionsdataarchive",
            name="data",
            field=transit_odp.common.fields.CallableStorageFileField(
                help_text="A zip file containing an up to date SIRI-SX XML.",
                storage=transit_odp.disruptions.storage.get_sirisx_storage,
                upload_to="",
            ),
        ),
    ]