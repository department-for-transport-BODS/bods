# Generated by Django 2.2.7 on 2019-11-18 10:29

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data_quality", "0008_auto_20191115_1312"),
    ]

    operations = [
        migrations.RenameField(
            model_name="servicepattern",
            old_name="geom",
            new_name="geometry",
        ),
    ]
