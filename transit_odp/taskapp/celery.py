import os
from typing import Final

from celery import Celery
from celery.schedules import crontab
from django.apps import AppConfig, apps
from django.conf import settings

if not settings.configured:
    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "config.settings.local"
    )  # pragma: no cover

app = Celery("transit_odp")

TIMETABLE_TASKS: Final = "transit_odp.timetables.tasks."
PIPELINE_TASKS: Final = "transit_odp.pipelines.tasks."
AVL_TASKS: Final = "transit_odp.avl.tasks."


class CeleryAppConfig(AppConfig):
    name = "transit_odp.taskapp"
    verbose_name = "Celery Config"

    def ready(self):
        # Using a string here means the worker will not have to
        # pickle the object when using Windows.
        # - namespace='CELERY' means all celery-related configuration keys
        #   should have a `CELERY_` prefix.
        app.config_from_object("django.conf:settings", namespace="CELERY")
        installed_apps = [app_config.name for app_config in apps.get_app_configs()]
        app.autodiscover_tasks(lambda: installed_apps, force=True)

        app.conf.beat_schedule = {
            "monitor_feeds": {
                "task": TIMETABLE_TASKS + "task_update_remote_timetables",
                "schedule": crontab(minute=0, hour=4),
            },
            "monitor_feeds_afternoon": {
                "task": TIMETABLE_TASKS + "task_update_remote_timetables",
                "schedule": crontab(minute=0, hour=16),
            },
            "retry_unavailable_feeds": {
                "task": TIMETABLE_TASKS + "task_retry_unavailable_timetables",
                "schedule": crontab(minute=0),
            },
            # scheduled 1 hour after task_set_expired_feeds to ensure archive
            # excluded newly expired datasets
            "create_bulk_data_archive": {
                "task": PIPELINE_TASKS + "task_create_bulk_data_archive",
                "schedule": crontab(minute=0, hour=6),
            },
            # scheduled 1 hour after task_set_expired_feeds to ensure archive
            # excluded newly expired datasets
            "create_change_data_archive": {
                "task": PIPELINE_TASKS + "task_create_change_data_archive",
                "schedule": crontab(minute=0, hour=6),
            },
            # scheduled at 1am and this task should be the first that runs
            # before other tasks
            "run_naptan_etl": {
                "task": PIPELINE_TASKS + "task_run_naptan_etl",
                "schedule": crontab(minute=0, hour=1),
            },
            "dqs_monitor": {
                "task": PIPELINE_TASKS + "task_dqs_monitor",
                "schedule": 10.0,
            },
            "monitor_avl_feeds": {
                "task": PIPELINE_TASKS + "task_monitor_avl_feeds",
                "schedule": 30.0,
            },
            "create_siri_zip": {
                "task": AVL_TASKS + "task_create_sirivm_zipfile",
                "schedule": 10.0,
            },
            "create_gtfsrt_zip": {
                "task": AVL_TASKS + "task_create_gtfsrt_zipfile",
                "schedule": 10.0,
            },
            "save_operational_stats": {
                "task": "transit_odp.site_admin.tasks.task_save_operational_stats",
                "schedule": crontab(minute=0, hour=23),
            },
        }

        if hasattr(settings, "RAVEN_CONFIG"):
            # Celery signal registration
            # Since raven is required in production only,
            # imports might (most surely will) be wiped out
            # during PyCharm code clean up started
            # in other environments.
            # @formatter:off
            from raven import Client as RavenClient
            from raven.contrib.celery import (
                register_logger_signal as raven_register_logger_signal,
            )
            from raven.contrib.celery import register_signal as raven_register_signal

            # @formatter:on

            raven_client = RavenClient(dsn=settings.RAVEN_CONFIG["dsn"])
            raven_register_logger_signal(raven_client)
            raven_register_signal(raven_client)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")  # pragma: no cover
