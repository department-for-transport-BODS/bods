# Generated by Django 4.2.14 on 2025-06-16 08:02

from django.db import migrations, models
import transit_odp.publish.validators


class Migration(migrations.Migration):

    dependencies = [
        ("organisation", "0074_datasetrevision_modified_before_reprocessing_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datasetrevision",
            name="upload_file",
            field=models.FileField(
                blank=True,
                max_length=256,
                null=True,
                upload_to="",
                validators=[transit_odp.publish.validators.validate_file_extension],
                verbose_name="Name of the uploaded file, if any",
            ),
        ),
    ]
