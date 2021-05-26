from django.apps import AppConfig


class RestrictedSessions(AppConfig):
    name = "transit_odp.restrict_sessions"
    verbose_name = "Restricted Sessions"
    # This function is the only new thing in this file
    # it just imports the signal file when the app is ready

    def ready(self):
        import transit_odp.restrict_sessions.signals  # noqa F401
