from django.apps import AppConfig
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


def configure_waffle_flags(sender, **kwargs):
    from waffle.models import Flag

    # Check if the flag exists
    flag, created = Flag.objects.get_or_create(name="is_timetable_visualiser_active")

    # Set the flag to True (activate the feature)
    flag.active = True
    flag.everyone = True
    flag.testing = True
    flag.superusers = True
    flag.staff = True
    flag.authenticated = True
    flag.save()


class PipelinesConfig(AppConfig):
    name = "transit_odp.pipelines"

    def ready(self):
        import transit_odp.pipelines.receivers  # noqa: F401

        post_migrate.connect(configure_waffle_flags, sender=self)
