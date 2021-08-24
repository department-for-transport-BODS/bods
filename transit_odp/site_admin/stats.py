from logging import getLogger

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from pydantic import BaseModel
from requests.exceptions import RequestException

from transit_odp.organisation.constants import (
    AVLFeedStatus,
    AVLType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.models import Dataset, Organisation
from transit_odp.users.constants import (
    AgentUserType,
    DeveloperType,
    OrgAdminType,
    OrgStaffType,
)

Expired = FeedStatus.expired.value
Inactive = FeedStatus.inactive.value
FeedUp = AVLFeedStatus.FEED_UP

User = get_user_model()
logger = getLogger(__name__)


class ConsumerAPIStats(BaseModel):
    version: str
    query_time: float
    num_of_gtfs_rt_vehicles: int
    num_of_siri_vehicles: int


def get_operator_count():
    """Returns the number of currently active Organisations."""
    return Organisation.objects.filter(is_active=True).count()


def get_user_counts():
    """Returns a dictionary containing counts of organisation user, agent users and
    consumers.
    """
    active_org = Q(organisations__is_active=True)
    is_org_user = Q(account_type__in=[OrgAdminType, OrgStaffType])
    user_counts = User.objects.filter(is_active=True).aggregate(
        operator_user_count=Count("pk", filter=active_org & is_org_user),
        agent_user_count=Count("pk", filter=Q(account_type=AgentUserType)),
        consumer_count=Count("pk", filter=Q(account_type=DeveloperType)),
    )
    return user_counts


def get_active_dataset_counts():
    """Returns a dictionary containing the counts of all the active timetables,
    avl feeds and fares datasets.
    """
    dataset_counts = (
        Dataset.objects.get_active()
        .filter(organisation__is_active=True)
        .aggregate(
            timetables_count=Count("pk", filter=Q(dataset_type=TimetableType)),
            avl_count=Count("pk", filter=Q(dataset_type=AVLType)),
            fares_count=Count("pk", filter=Q(dataset_type=FaresType)),
        )
    )
    return dataset_counts


def get_orgs_with_active_dataset_counts():
    """Returns a dictionary of the counts for all the organisations that have
    at least one published dataset type.
    """
    is_org_active = Q(is_active=True)
    has_live_revision = Q(dataset__live_revision__isnull=False)
    revision_is_active = ~Q(dataset__live_revision__status__in=[Inactive, Expired])

    active_org_counts = (
        Organisation.objects.filter(
            is_org_active & has_live_revision & revision_is_active
        )
        .annotate(
            timetable=Count("dataset", filter=Q(dataset__dataset_type=TimetableType)),
            avl=Count("dataset", filter=Q(dataset__dataset_type=AVLType)),
            fares=Count("dataset", filter=Q(dataset__dataset_type=FaresType)),
        )
        .aggregate(
            published_timetable_operator_count=Count("pk", filter=Q(timetable__gt=0)),
            published_avl_operator_count=Count("pk", filter=Q(avl__gt=0)),
            published_fares_operator_count=Count("pk", filter=Q(fares__gt=0)),
        )
    )
    return active_org_counts


def get_siri_vm_vehicle_counts() -> int:
    stats_url = settings.CAVL_CONSUMER_URL + "/stats"
    vehicle_counts = 0

    try:
        response = requests.get(stats_url, timeout=60)
    except RequestException as exc:
        logger.error("Request to stats api failed.", exc_info=exc)
    else:
        if response.status_code == 200:
            api_stats = ConsumerAPIStats(**response.json())
            vehicle_counts = api_stats.num_of_siri_vehicles

    return vehicle_counts
