# Generated by Django 2.2.5 on 2019-10-03 10:38

import django.db.models.deletion
import django_extensions.db.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisation", "0004_auto_20191003_1131"),
    ]

    operations = [
        migrations.CreateModel(
            name="DatasetSubscription",
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
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="dataset",
            name="subscribers",
            field=models.ManyToManyField(
                related_name="subscriptions",
                through="organisation.DatasetSubscription",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.DeleteModel(name="FeedSubscriber"),
        migrations.AddField(
            model_name="datasetsubscription",
            name="dataset",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="organisation.Dataset",
            ),
        ),
        migrations.AddField(
            model_name="datasetsubscription",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterUniqueTogether(
            name="datasetsubscription", unique_together={("dataset", "user")}
        ),
    ]
