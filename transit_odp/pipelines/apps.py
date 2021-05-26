from django.apps import AppConfig


class PipelinesConfig(AppConfig):
    name = "transit_odp.pipelines"

    def ready(self):
        import transit_odp.pipelines.receivers  # noqa: F401
