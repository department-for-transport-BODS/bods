import logging

import requests
from django.conf import settings
from django.db.models import Q

from transit_odp.common.enums import FeedErrorCategory, FeedErrorSeverity
from transit_odp.organisation import signals
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import Dataset
from transit_odp.organisation.querysets import DatasetQuerySet
from transit_odp.pipelines.models import DatasetETLError
from transit_odp.pipelines.signals import dataset_changed

logger = logging.getLogger(__name__)


def monitor_available_feeds():
    """Monitor all Timetable Dataset URLs."""
    logger.info("[DatasetMonitoring]: Started.")
    count_is_zero = Q(live_revision__availability_retry_count__count=0)
    count_is_null = Q(live_revision__availability_retry_count__isnull=True)
    datasets = Dataset.objects.filter(
        count_is_zero | count_is_null, dataset_type=DatasetType.TIMETABLE.value
    )
    monitor_feeds(datasets)


def retry_unavailable_feeds():
    """Retry previously unavailable dataset URLs."""
    logger.info("[DatasetMonitoring] => Checking previously unavailable datasets.")
    datasets = Dataset.objects.filter(
        dataset_type=DatasetType.TIMETABLE.value,
        live_revision__availability_retry_count__count__gt=0,
    )
    monitor_feeds(datasets)


def monitor_feeds(datasets: DatasetQuerySet):
    logger.info("[DatasetMonitoring] => Starting dataset monitoring")
    exclude_status = [FeedStatus.expired.value, FeedStatus.inactive.value]
    datasets = (
        datasets.get_active()
        .get_remote()
        .select_related("live_revision__availability_retry_count")
        .exclude(live_revision__status__in=exclude_status)
    )

    logger.info(f"[DatasetMonitoring] => monitoring {len(datasets)} datasets")

    for dataset in datasets:
        try:
            monitor_feed(dataset)
        except Exception as err:
            # if Exception is thrown continue processing other datasets
            logger.error("[DatasetMonitoring] => ", err)


def monitor_feed(dataset):
    logger.info(f"[DatasetMonitoring] Dataset {dataset.id} => Should I update dataset?")
    data = fetch_data(dataset.live_revision.url_link)
    if data is not None:
        handle_feed_available(dataset, data)
    else:
        handle_feed_unavailable(dataset)


def fetch_data(url):
    _prefix = f"[DatasetMonitoring] Dataset URL {url} => "
    logger.info(_prefix + "Fetching data.")
    try:
        r = requests.get(url)
        logger.info(_prefix + f"Request returned with status code: {r.status_code}")
        if r.ok:
            return r.content
    except requests.exceptions.ConnectionError as e:
        logger.error(_prefix + "ConnectionError", e)
        # TODO - implement retry to make this robust against normal network failures

    return None


def handle_feed_available(dataset, data):
    _prefix = f"[DatasetMonitoring] Dataset {dataset.id} => "
    logger.info(_prefix + "Handling dataset available.")

    retry_count = dataset.get_availability_retry_count()

    old_hash = dataset.get_hash()
    new_hash = dataset.compute_hash(data)

    if old_hash != new_hash:
        logger.info(_prefix + "Data has has changed.")
        reindex_feed(dataset)
        signals.feed_monitor_change_detected.send(None, dataset=dataset)
    elif retry_count.count > 0:
        logger.info(_prefix + "Connected to URL. Resetting counter.")
        signals.feed_monitor_dataset_available.send(None, dataset=dataset)

    logger.info(_prefix + "Resetting counter.")
    retry_count.reset()


def handle_feed_unavailable(dataset):
    _prefix = f"[DatasetMonitoring] Dataset {dataset.id} => "
    logger.info(_prefix + "Handling unavailable URL.")

    max_retries = settings.FEED_MONITOR_MAX_RETRY_ATTEMPTS
    retry_count = dataset.get_availability_retry_count()
    retry_count.count += 1
    retry_count.save()

    logger.info(
        _prefix + f"Failed to access URL, count incremented to {retry_count.count}."
    )

    if retry_count.count == 1:
        # signal - send first notification that url is unreachable and will be re-tried
        signals.feed_monitor_fail_first_try.send(None, dataset=dataset)
        logger.info(_prefix + "First retry of URL.")
    elif retry_count.count >= max_retries:
        # signal - send second notification that url is unreachable even after re-try
        signals.feed_monitor_fail_final_try.send(None, dataset=dataset)
        logger.info(
            _prefix + f"Retry limit of {max_retries} reached, marking as unavailable."
        )

        # delete existing errors & add availability error
        DatasetETLError.objects.filter(revision=dataset.live_revision).delete()
        DatasetETLError.objects.create(
            revision=dataset.live_revision,
            severity=FeedErrorSeverity.severe.value,
            category=FeedErrorCategory.availability.value,
            description="Data set is not reachable",
        )

        # set feed to archived
        dataset.live_revision.to_expired()
        dataset.live_revision.save()
        signals.feed_expired.send(None, dataset=dataset)


def reindex_feed(dataset):
    """Calls out to re-index the feed"""
    _prefix = f"[DatasetMonitoring] Dataset {dataset.id} => "
    logger.info(_prefix + "Reindexing dataset.")
    new_revision = dataset.start_revision(
        comment="Automatically detected change in data set"
    )
    new_revision.save()
    dataset_changed.send(None, revision=new_revision)
