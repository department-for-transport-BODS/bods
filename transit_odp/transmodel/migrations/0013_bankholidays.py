# Generated by Django 4.2.7 on 2024-02-07 12:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transmodel", "0012_remove_flexibleserviceoperationperiod_end_date_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="BankHolidays",
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
                ("txc_element", models.CharField(max_length=255)),
                ("title", models.CharField(blank=True, max_length=255, null=True)),
                ("date", models.DateField()),
                ("notes", models.CharField(blank=True, max_length=255, null=True)),
                ("division", models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
    ]
