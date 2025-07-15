from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("transmodel", "0040_remove_tracks_unique_from_to_atco_code"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX CONCURRENTLY idx_transmodel_vehiclejourney_blocknumber 
            ON transmodel_vehiclejourney (block_number);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS idx_transmodel_vehiclejourney_blocknumber;
            """,
        ),
    ]
