import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from transit_odp.notifications import get_notifications
from transit_odp.organisation.models import (
    ConsumerStats,
    Dataset,
    DatasetRevision,
    Organisation,
)
from transit_odp.organisation.notifications import (
    send_endpoint_available_notification,
    send_feed_changed_notification,
    send_feed_monitor_fail_final_try_notification,
    send_feed_monitor_fail_first_try_notification,
    send_revision_published_notification,
)
from transit_odp.organisation.signals import (
    feed_monitor_change_detected,
    feed_monitor_dataset_available,
    feed_monitor_fail_final_try,
    feed_monitor_fail_first_try,
    revision_publish,
)

logger = logging.getLogger(__name__)
client = get_notifications()


@receiver(post_save, sender=DatasetRevision)
def update_live_revision(sender, instance: DatasetRevision, **kwargs):
    # Note this would be more performant as a database trigger
    current = instance.tracker.current()["is_published"]
    if not instance.tracker.previous("is_published") and current is True:
        dataset = instance.dataset
        dataset.live_revision = instance
        dataset.save()


@receiver(feed_monitor_fail_first_try)
def feed_monitor_fail_first_try_handler(sender, dataset: Dataset, **kwargs):
    logger.debug(
        f"[feed_monitor_fail_first_try_handler] received signal for "
        f"Dataset<id={dataset.id}>"
    )
    send_feed_monitor_fail_first_try_notification(dataset)


@receiver(feed_monitor_fail_final_try)
def feed_monitor_fail_final_try_handler(sender, dataset: Dataset, **kwargs):
    logger.debug(
        f"[feed_monitor_fail_final_try_handler] received signal for "
        f"Dataset<id={dataset.id}>"
    )
    send_feed_monitor_fail_final_try_notification(dataset)


@receiver(feed_monitor_change_detected)
def feed_monitor_change_detected_handler(sender, dataset: Dataset, **kwargs):
    logger.debug(
        f"[feed_monitor_change_detected_handler] received a "
        f"signal for Dataset<id={dataset.id}>"
    )
    send_feed_changed_notification(dataset)


@receiver(feed_monitor_dataset_available)
def feed_monitor_dataset_available_handler(sender, dataset: Dataset, **kwargs):
    logger.debug(
        f"[feed_monitor_dataset_available_handler] received a signal "
        f"for Dataset<id={dataset.id}>"
    )
    send_endpoint_available_notification(dataset)


@receiver(revision_publish)
def revision_publish_handler(sender, dataset: Dataset, **kwargs):
    logger.debug(
        f"[revision_publish_handler] received a signal for "
        f"DatasetRevision<id={dataset.live_revision.id}>"
    )
    send_revision_published_notification(dataset)


@receiver(post_save, sender=Organisation)
def create_consumer_stats(sender, instance=None, created=False, **kwargs):
    if created:
        ConsumerStats.objects.create(organisation=instance)
