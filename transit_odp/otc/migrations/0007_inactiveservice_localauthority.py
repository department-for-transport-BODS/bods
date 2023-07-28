# Generated by Django 3.2.16 on 2023-07-18 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('otc', '0006_auto_20230331_1028'),
    ]

    operations = [
        migrations.CreateModel(
            name='InactiveService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_number', models.CharField(max_length=20, unique=True)),
                ('registration_status', models.CharField(blank=True, max_length=20)),
                ('effective_date', models.DateField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='LocalAuthority',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(blank=True, unique=True)),
                ('ui_lta_name', models.CharField(blank=True, max_length=255, null=True)),
                ('atco_code', models.IntegerField(blank=True, null=True)),
                ('registration_numbers', models.ManyToManyField(related_name='registration', to='otc.Service')),
            ],
            options={
                'verbose_name': 'Local Authority',
                'verbose_name_plural': 'Local Authorities',
            },
        ),
    ]
