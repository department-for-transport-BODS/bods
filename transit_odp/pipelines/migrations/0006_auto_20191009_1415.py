# Generated by Django 2.2.5 on 2019-10-09 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("pipelines", "0005_bulkdataarchive")]

    operations = [
        migrations.CreateModel(
            name="ChangeDataArchive",
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
                    "published_at",
                    models.DateField(
                        help_text="The date of publication", verbose_name="published_at"
                    ),
                ),
                (
                    "data",
                    models.FileField(
                        help_text="A zip file containing all datasets published at 'published_at'",
                        upload_to="",
                    ),
                ),
            ],
            options={"ordering": ("-published_at",), "get_latest_by": "-published_at"},
        ),
        migrations.AlterModelOptions(
            name="bulkdataarchive",
            options={"get_latest_by": "-created", "ordering": ("-created",)},
        ),
        migrations.RemoveField(model_name="bulkdataarchive", name="modified"),
    ]
