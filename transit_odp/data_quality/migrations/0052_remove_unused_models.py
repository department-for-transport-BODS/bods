# Generated by Django 2.2.19 on 2021-05-04 09:46

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data_quality", "0051_added_schema_violation_model"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="schemanottxc24warning",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="schemanottxc24warning",
            name="report",
        ),
        migrations.DeleteModel(
            name="MissingNOCWarning",
        ),
        migrations.DeleteModel(
            name="SchemaNotTXC24Warning",
        ),
    ]
