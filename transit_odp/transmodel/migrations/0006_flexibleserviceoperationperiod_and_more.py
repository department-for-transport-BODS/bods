# Generated by Django 4.1.13 on 2024-01-24 21:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("transmodel", "0005_auto_20231117_1055"),
    ]

    operations = [
        migrations.CreateModel(
            name="FlexibleServiceOperationPeriod",
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
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="NonOperatingDatesExceptions",
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
                ("non_operating_date", models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="OperatingDatesExceptions",
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
                ("operating_date", models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="OperatingProfile",
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
                    "day_of_week",
                    models.CharField(
                        choices=[
                            ("Monday", "Monday"),
                            ("Tuesday", "Tuesday"),
                            ("Wednesday", "Wednesday"),
                            ("Thursday", "Thursday"),
                            ("Friday", "Friday"),
                            ("Saturday", "Saturday"),
                            ("Sunday", "Sunday"),
                        ],
                        max_length=20,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ServicedOrganisations",
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
                ("name", models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="ServicedOrganisationVehicleJourney",
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
                ("operating_on_working_days", models.BooleanField(default=False)),
                (
                    "serviced_organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transmodel.servicedorganisations",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ServicedOrganisationWorkingDays",
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
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                (
                    "serviced_organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="serviced_organisations_working_days",
                        to="transmodel.servicedorganisations",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="servicepatternstop",
            name="departure_time",
            field=models.TimeField(default=None, null=True),
        ),
        migrations.AddField(
            model_name="servicepatternstop",
            name="is_timing_point",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="servicepatternstop",
            name="txc_common_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="vehiclejourney",
            name="direction",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="vehiclejourney",
            name="journey_code",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="vehiclejourney",
            name="line_ref",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.DeleteModel(
            name="TimingPatternStop",
        ),
        migrations.AddField(
            model_name="servicedorganisationvehiclejourney",
            name="vehicle_journey",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="transmodel.vehiclejourney",
            ),
        ),
        migrations.AddField(
            model_name="servicedorganisations",
            name="vehicle_journeys",
            field=models.ManyToManyField(
                related_name="serviced_organisations",
                through="transmodel.ServicedOrganisationVehicleJourney",
                to="transmodel.vehiclejourney",
            ),
        ),
        migrations.AddField(
            model_name="operatingprofile",
            name="vehicle_journey",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="operating_profiles",
                to="transmodel.vehiclejourney",
            ),
        ),
        migrations.AddField(
            model_name="operatingdatesexceptions",
            name="vehicle_journey",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="operating_dates_exceptions",
                to="transmodel.vehiclejourney",
            ),
        ),
        migrations.AddField(
            model_name="nonoperatingdatesexceptions",
            name="vehicle_journey",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="non_operating_dates_exceptions",
                to="transmodel.vehiclejourney",
            ),
        ),
        migrations.AddField(
            model_name="flexibleserviceoperationperiod",
            name="vehicle_journey",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="flexible_service_operation_period",
                to="transmodel.vehiclejourney",
            ),
        ),
    ]
