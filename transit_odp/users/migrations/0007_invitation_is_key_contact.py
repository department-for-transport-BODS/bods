# Generated by Django 2.2.9 on 2020-01-27 17:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_user_privacy_consent"),
    ]

    operations = [
        migrations.AddField(
            model_name="invitation",
            name="is_key_contact",
            field=models.BooleanField(default=False),
        ),
    ]
