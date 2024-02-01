from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


class PipelinesConfig(AppConfig):
    name = "transit_odp.pipelines"

    def ready(self):
        import transit_odp.pipelines.receivers  # noqa: F401
