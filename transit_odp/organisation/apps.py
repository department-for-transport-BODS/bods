from django.apps import AppConfig


class OrganisationConfig(AppConfig):
    name = "transit_odp.organisation"

    def ready(self):
        import transit_odp.organisation.receivers  # noqa
