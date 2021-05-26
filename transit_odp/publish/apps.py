from django.apps import AppConfig


class PublishConfig(AppConfig):
    name = "transit_odp.publish"
    verbose_name = "Publish"

    def ready(self):
        pass
