# Generated by Django 2.2.19 on 2021-03-25 11:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_quality", "0048_ptiobservation"),
    ]

    operations = [
        migrations.AddField(
            model_name="ptiobservation",
            name="reference",
            field=models.CharField(
                default="0.0",
                help_text="The section that details this observation.",
                max_length=64,
            ),
        ),
    ]
