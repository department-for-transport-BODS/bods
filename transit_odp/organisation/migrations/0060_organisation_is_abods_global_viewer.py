# Generated by Django 4.2.9 on 2024-05-28 08:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organisation", "0059_alter_dataset_dataset_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="organisation",
            name="is_abods_global_viewer",
            field=models.BooleanField(
                default=False,
                help_text="Whether organisation will be used solely for managing ABODS global viewer users",
            ),
        ),
    ]