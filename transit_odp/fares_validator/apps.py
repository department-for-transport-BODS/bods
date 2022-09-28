from django.apps import AppConfig


class FaresValidatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "transit_odp.fares_validator"
    verbose_name = "fares_validator"
