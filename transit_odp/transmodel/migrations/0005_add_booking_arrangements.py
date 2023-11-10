# Generated by Django 3.2.20 on 2023-11-10 14:55

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('transmodel', '0004_auto_20191112_1151'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingArrangements',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='email address')),
                ('phone_number', models.CharField(blank=True, max_length=16, null=True)),
                ('web_address', models.URLField(blank=True, null=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('last_updated', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='last_updated')),
                ('service_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_arrangements', to='transmodel.service')),
            ],
            options={
                'ordering': ('service_id', 'last_updated'),
            },
        ),
        migrations.AddConstraint(
            model_name='bookingarrangements',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('email__exact', ''), ('email__isnull', False)), models.Q(('phone_number__exact', ''), ('phone_number__isnull', False)), models.Q(('web_address__exact', ''), ('web_address__isnull', False)), _connector='OR'), name='at_least_one_column_not_null_or_empty'),
        ),
    ]
