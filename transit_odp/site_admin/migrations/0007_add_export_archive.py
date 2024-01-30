# Generated by Django 2.2.24 on 2021-06-28 11:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("site_admin", "0006_auto_20210506_1717"),
    ]

    operations = [
        migrations.CreateModel(
            name="MetricsArchive",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start", models.DateField()),
                ("end", models.DateField()),
                ("archive", models.FileField(upload_to="")),
            ],
        ),
    ]
