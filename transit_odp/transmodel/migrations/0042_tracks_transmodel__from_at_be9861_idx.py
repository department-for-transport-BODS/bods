# Generated by Django 4.2.23 on 2025-07-16 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transmodel", "0041_auto_20250715_0957"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="tracks",
            index=models.Index(
                fields=["from_atco_code", "to_atco_code"],
                name="transmodel__from_at_be9861_idx",
            ),
        ),
    ]
