# Generated by Django 2.2.5 on 2019-09-30 08:49

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisation", "0001_initial"),
        ("naptan", "0001_initial"),
        ("django_celery_results", "0004_auto_20190516_0412"),
    ]

    operations = [
        migrations.AddField(
            model_name="feedsubscriber",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="feed_subscriber",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="feederrors",
            name="revision",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="errors",
                to="organisation.DatasetRevision",
            ),
        ),
        migrations.AddField(
            model_name="datasetrevision",
            name="admin_areas",
            field=models.ManyToManyField(
                related_name="revisions", to="naptan.AdminArea"
            ),
        ),
        migrations.AddField(
            model_name="datasetrevision",
            name="dataset",
            field=models.ForeignKey(
                help_text="The parent dataset",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="revisions",
                to="organisation.Dataset",
            ),
        ),
        migrations.AddField(
            model_name="datasetrevision",
            name="last_modified_user",
            field=models.ForeignKey(
                blank=True,
                help_text="Bus portal organisation.",
                null=True,
                on_delete=None,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="datasetrevision",
            name="localities",
            field=models.ManyToManyField(
                related_name="revisions", to="naptan.Locality"
            ),
        ),
        migrations.AddField(
            model_name="datasetrevision",
            name="published_by",
            field=models.ForeignKey(
                blank=True,
                help_text="The user that made this change",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="publications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="datasetrevision",
            name="task_progress",
            field=models.ManyToManyField(
                through="organisation.FeedTaskResult",
                to="django_celery_results.TaskResult",
            ),
        ),
        migrations.AddField(
            model_name="dataset",
            name="live_revision",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="live_revision_dataset",
                to="organisation.DatasetRevision",
            ),
        ),
        migrations.AddField(
            model_name="dataset",
            name="organisation",
            field=models.ForeignKey(
                help_text="Bus portal organisation.",
                on_delete=django.db.models.deletion.CASCADE,
                to="organisation.Organisation",
            ),
        ),
        migrations.AddField(
            model_name="dataset",
            name="subscribers",
            field=models.ManyToManyField(
                related_name="subscriptions",
                through="organisation.FeedSubscriber",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="LiveDatasetRevision",
            fields=[],
            options={
                "abstract": False,
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("organisation.datasetrevision",),
        ),
        migrations.AlterUniqueTogether(
            name="feedsubscriber", unique_together={("dataset", "user")}
        ),
        migrations.AddIndex(
            model_name="datasetrevision",
            index=models.Index(
                fields=["is_published"], name="organisatio_is_publ_bee2ff_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="datasetrevision",
            constraint=models.UniqueConstraint(
                fields=("dataset", "created"),
                name="organisation_datasetrevision_unique_revision",
            ),
        ),
        migrations.AddConstraint(
            model_name="datasetrevision",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_published=False),
                fields=("dataset",),
                name="organisation_datasetrevision_unique_draft_revision",
            ),
        ),
    ]
