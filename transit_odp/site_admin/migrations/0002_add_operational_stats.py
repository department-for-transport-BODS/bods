# Generated by Django 2.2.13 on 2020-11-17 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("site_admin", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationalStats",
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
                ("date", models.DateField(unique=True)),
                ("operator_count", models.IntegerField()),
                ("operator_user_count", models.IntegerField()),
                ("agent_user_count", models.IntegerField()),
                ("consumer_count", models.IntegerField()),
                ("timetables_count", models.IntegerField()),
                ("avl_count", models.IntegerField()),
                ("fares_count", models.IntegerField()),
                ("published_timetable_operator_count", models.IntegerField()),
                ("published_avl_operator_count", models.IntegerField()),
                ("published_fares_operator_count", models.IntegerField()),
            ],
        ),
    ]
