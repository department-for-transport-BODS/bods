# Generated by Django 3.2.20 on 2023-12-15 10:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('otc', '0011_auto_20231213_1054'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='localauthority',
            name='atco_code',
        ),
    ]
