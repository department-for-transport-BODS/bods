from celery import shared_task
from django.utils import timezone

from transit_odp.site_admin.models import OperationalStats
from transit_odp.site_admin.stats import (
    get_active_dataset_counts,
    get_operator_count,
    get_orgs_with_active_dataset_counts,
    get_user_counts,
)


@shared_task()
def task_save_operational_stats():
    """A task to save operational stats for the current day

    date: todays date

    operator_count: number of active operators

    operator_user_count: number of active org admins + org staff in active orgs
    agent_user_count: number of active agent users
    consumer_count: number of active consumer users

    timetables_count: total number of active timetables from active orgs
    avl_count: total number of active avl feeds (regardless of status) from
        active orgs
    fares_count: total number of active fares from active orgs

    published_timetable_operator_count: number of operators with active
        timetables
    published_avl_operator_count: number of operators with active avl feeds
    published_fares_operator_count: number of operators with active fares

    """
    date = timezone.now().date()
    stats = {"operator_count": get_operator_count()}
    stats.update(get_user_counts())
    stats.update(get_active_dataset_counts())
    stats.update(get_orgs_with_active_dataset_counts())

    OperationalStats.objects.update_or_create(date=date, defaults=stats)
