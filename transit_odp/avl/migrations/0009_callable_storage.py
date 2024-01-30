# Generated by Django 2.2.13 on 2020-10-02 11:26

from django.db import migrations

import transit_odp.avl.storage
import transit_odp.common.fields


class Migration(migrations.Migration):
    dependencies = [
        ("avl", "0008_auto_20200928_2141"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cavldataarchive",
            name="data",
            field=transit_odp.common.fields.CallableStorageFileField(
                help_text="A zip file containing an up to date siri vm XML.",
                storage=transit_odp.avl.storage.get_sirivm_storage,
                upload_to="",
            ),
        ),
    ]
