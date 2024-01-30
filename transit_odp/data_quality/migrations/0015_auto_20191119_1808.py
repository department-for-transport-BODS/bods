# Generated by Django 2.2.7 on 2019-11-19 18:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_quality", "0014_auto_20191119_0217"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="stoppoint",
            options={"ordering": ("atco_code", "is_provisional")},
        ),
        migrations.AddField(
            model_name="stoppoint",
            name="is_provisional",
            field=models.BooleanField(
                default=False,
                help_text="The stop is provisional and not yet officially in NapTaN",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="stoppoint",
            unique_together={("atco_code", "is_provisional")},
        ),
    ]
