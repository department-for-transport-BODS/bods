from django.apps import AppConfig


class UsersAppConfig(AppConfig):

    name = "transit_odp.users"
    verbose_name = "Users"

    def ready(self):
        try:
            import transit_odp.users.receivers  # noqa F401
        except ImportError:
            pass
