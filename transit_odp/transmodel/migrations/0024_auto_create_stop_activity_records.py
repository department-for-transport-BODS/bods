from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("transmodel", "0022_alter_vehiclejourney_block_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicepatternstop",
            name="stop_activity",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="stop_activity",
                to="transmodel.stopactivity",
            ),
        ),
    ]
