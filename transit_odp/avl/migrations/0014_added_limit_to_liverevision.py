# Generated by Django 3.0.14 on 2021-08-12 15:42

import django.db.models.deletion
import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organisation", "0046_added_licence_model"),
        ("avl", "0013_added_positive_int_constraint_and_unique_constraint"),
    ]

    operations = [
        migrations.AlterField(
            model_name="avlvalidationreport",
            name="revision",
            field=models.ForeignKey(
                limit_choices_to=models.Q(
                    ("dataset__dataset_type", 2),
                    ("dataset__live_revision_id", django.db.models.expressions.F("id")),
                ),
                on_delete=django.db.models.deletion.CASCADE,
                related_name="avl_validation_reports",
                to="organisation.DatasetRevision",
            ),
        ),
    ]
