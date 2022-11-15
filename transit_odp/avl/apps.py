from django.apps import AppConfig


class AvlConfig(AppConfig):
    name = "transit_odp.avl"
    verbose_name = "Avl"

    def ready(self):
        from transit_odp.avl import signals  # noqa: F401
