# Generated by Django 4.2.14 on 2025-01-30 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transmodel", "0033_alter_servicepatternstop_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="servicepattern",
            name="line_name",
            field=models.CharField(
                blank=True, db_index=True, max_length=255, null=True
            ),
        ),
    ]
