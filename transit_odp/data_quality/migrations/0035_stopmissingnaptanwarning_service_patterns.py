# Generated by Django 2.2.8 on 2019-12-04 13:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_quality", "0034_merge_20191204_1021"),
    ]

    operations = [
        migrations.AddField(
            model_name="stopmissingnaptanwarning",
            name="service_patterns",
            field=models.ManyToManyField(to="data_quality.ServicePattern"),
        ),
    ]
