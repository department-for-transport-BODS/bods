# Generated by Django 4.2.14 on 2024-10-29 13:27

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organisation", "0066_datasetrevision_modified_file_hash_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="servicecodeexemption",
            name="registration_code",
            field=models.CharField(
                help_text="The part of the service code after the licence prefix",
                max_length=50,
                validators=[
                    django.core.validators.RegexValidator(
                        "^\\d+$", "Only numeric values are allowed."
                    )
                ],
            ),
        ),
    ]
