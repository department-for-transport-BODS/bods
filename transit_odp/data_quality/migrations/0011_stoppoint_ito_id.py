# Generated by Django 2.2.7 on 2019-11-18 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_quality", "0010_auto_20191118_1604"),
    ]

    operations = [
        migrations.AddField(
            model_name="stoppoint",
            name="ito_id",
            field=models.TextField(default=None, unique=True),
            preserve_default=False,
        ),
    ]
