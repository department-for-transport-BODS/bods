from django.db import migrations, models

from transit_odp.common.db.bigint_pk import PkSpec, Tuning, convert_pk_to_bigint


def convert_id_to_bigint(apps, schema_editor):
    convert_pk_to_bigint(
        schema_editor.connection,
        PkSpec(table="site_admin_apirequest"),
        Tuning.from_env(),
    )


class Migration(migrations.Migration):
    # Online conversion: CREATE INDEX CONCURRENTLY and chunked backfill commits
    # can't run inside a transaction. A killed run resumes on the next migrate.
    atomic = False

    dependencies = [
        ("site_admin", "0017_add_unique_together_to_resource_counter"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Reverse is a DB no-op: bigint is a superset and AutoField works on it.
                migrations.RunPython(
                    convert_id_to_bigint, migrations.RunPython.noop, atomic=False
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="apirequest",
                    name="id",
                    field=models.BigAutoField(primary_key=True, serialize=False),
                ),
            ],
        ),
    ]
