# Generated by Django 2.2.6 on 2019-10-24 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("organisation", "0018_auto_20191024_1354")]

    operations = [
        migrations.AlterField(
            model_name="organisation",
            name="short_name",
            field=models.CharField(
                max_length=255, verbose_name="Organisation Short Name"
            ),
        )
    ]
