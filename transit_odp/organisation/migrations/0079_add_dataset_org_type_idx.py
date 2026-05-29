from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("organisation", "0078_datasetrevision_deletion_started_at_and_more"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="dataset",
            index=models.Index(
                fields=["organisation", "dataset_type"],
                name="org_dataset_org_type_idx",
            ),
        ),
    ]
