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

OTC_TASKS: Final = "transit_odp.otc.tasks."
PIPELINE_TASKS: Final = "transit_odp.pipelines.tasks."
TIMETABLE_TASKS: Final = "transit_odp.timetables.tasks."
AVL_TASKS: Final = "transit_odp.avl.tasks."
FARES_TASKS: Final = "transit_odp.fares.tasks."
ADMIN_TASKS: Final = "transit_odp.site_admin.tasks."
BROWSE_TASKS: Final = "transit_odp.browse.tasks."
PUBLISH_TASKS: Final = "transit_odp.publish.tasks."


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
            "monitor_fares_dataset": {
                "task": FARES_TASKS + "task_update_remote_fares",
                "schedule": crontab(minute=0, hour=4),
            },
            "monitor_fares_dataset_afternoon": {
                "task": FARES_TASKS + "task_update_remote_fares",
                "schedule": crontab(minute=0, hour=16),
            },
            "retry_unavailable_fares_datasets": {
                "task": FARES_TASKS + "task_retry_unavailable_fares",
                "schedule": crontab(minute=0),
            },
            # scheduled 1 hour after task_set_expired_feeds to ensure archive
            # excluded newly expired datasets
            "create_bulk_data_archive": {
                "task": BROWSE_TASKS + "task_create_bulk_data_archive",
                "schedule": crontab(minute=0, hour=6),
            },
            # scheduled 1 hour after task_set_expired_feeds to ensure archive
            # excluded newly expired datasets
            "create_change_data_archive": {
                "task": BROWSE_TASKS + "task_create_change_data_archive",
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
                "schedule": 60.0,
            },
            "update_bods_xsd_zip_files": {
                "task": PIPELINE_TASKS + "task_update_xsd_zip_cache",
                "schedule": crontab(
                    minute=0,
                    hour=0,
                    day_of_month=1,
                    month_of_year="*/3",
                    day_of_week="*",
                ),
            },
            "monitor_avl_feeds": {
                "task": AVL_TASKS + "task_monitor_avl_feeds",
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
            "create_siri_tfl_zip": {
                "task": AVL_TASKS + "task_create_sirivm_tfl_zipfile",
                "schedule": 10.0,
            },
            "log_stuck_tasks": {
                "task": TIMETABLE_TASKS + "task_log_stuck_revisions",
                "schedule": crontab(minute=0, hour=18),
            },
            "create_daily_api_stats": {
                "task": ADMIN_TASKS + "task_create_daily_api_stats",
                "schedule": crontab(minute=10, hour=0),
            },
            "save_operational_stats": {
                "task": ADMIN_TASKS + "task_save_operational_stats",
                "schedule": crontab(minute=0, hour=23),
            },
            "save_operational_exports": {
                "task": ADMIN_TASKS + "task_create_operational_exports_archive",
                "schedule": 1.0 * 60.0 * 60.0,
            },
            "task_delete_unwanted_data": {
                "task": ADMIN_TASKS + "task_delete_unwanted_data",
                "schedule": crontab(minute=45, hour=0),
            },
            "save_data_catalogue_exports": {
                "task": BROWSE_TASKS + "task_create_data_catalogue_archive",
                "schedule": 1.0 * 60.0 * 60.0,
            },
            "update_otc_data": {
                "task": OTC_TASKS + "task_refresh_otc_data",
                "schedule": crontab(minute=30, hour=23),
            },
            "refresh_monthly_breakdown_csv": {
                "task": PUBLISH_TASKS
                + "task_generate_monthly_consumer_interaction_breakdowns",
                "schedule": crontab(minute=40),
            },
            "refresh_weekly_consumer_interactions_stats": {
                "task": PUBLISH_TASKS + "task_generate_consumer_interaction_stats",
                "schedule": crontab(minute=55),
            },
            "weekly_post_publishing_checks_report": {
                "task": AVL_TASKS
                + "task_weekly_assimilate_post_publishing_check_reports",
                "schedule": crontab(day_of_week=0, hour=23, minute=0),
            },
            "task_seasonal_service_updated_dates": {
                "task": ADMIN_TASKS + "task_seasonal_service_updated_dates",
                "schedule": crontab(hour=23),
            },
        }
