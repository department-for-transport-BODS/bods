# Generated by Django 4.2.14 on 2025-01-30 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transmodel", "0034_alter_servicepattern_line_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="service",
            name="service_code",
            field=models.CharField(db_index=True, max_length=255),
        ),
    ]
