# Generated by Django 4.2.9 on 2024-06-26 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pipelines", "0023_alter_bulkdataarchive_dataset_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dataqualitytask",
            name="status",
            field=models.CharField(
                choices=[
                    ("FAILURE", "FAILURE"),
                    ("PENDING", "PENDING"),
                    ("READY", "READY"),
                    ("RECEIVED", "RECEIVED"),
                    ("STARTED", "STARTED"),
                    ("SUCCESS", "SUCCESS"),
                ],
                db_index=True,
                default="PENDING",
                help_text="Current state of the task being run",
                max_length=50,
                verbose_name="Task State",
            ),
        ),
        migrations.AlterField(
            model_name="datasetetltaskresult",
            name="status",
            field=models.CharField(
                choices=[
                    ("FAILURE", "FAILURE"),
                    ("PENDING", "PENDING"),
                    ("READY", "READY"),
                    ("RECEIVED", "RECEIVED"),
                    ("STARTED", "STARTED"),
                    ("SUCCESS", "SUCCESS"),
                ],
                db_index=True,
                default="PENDING",
                help_text="Current state of the task being run",
                max_length=50,
                verbose_name="Task State",
            ),
        ),
    ]
