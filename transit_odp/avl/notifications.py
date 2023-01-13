from django.utils import timezone

from transit_odp.avl.proxies import AVLDataset
from transit_odp.notifications import get_notifications
from transit_odp.notifications.client import INotifications
from transit_odp.organisation.models import Dataset

notifier: INotifications = get_notifications()


def send_avl_feed_down_notification(dataset: Dataset):
    if dataset.contact.settings.notify_avl_unavailable:
        notifier.send_avl_feed_down_publisher_notification(
            dataset_name=dataset.live_revision.name,
            dataset_id=dataset.id,
            short_description=dataset.live_revision.short_description,
            contact_email=dataset.contact.email,
        )


def send_avl_status_changed_notification(dataset: Dataset):
    for developer in dataset.subscribers.filter(
        settings__mute_all_dataset_notifications=False
    ):
        notifier.send_avl_feed_subscriber_notification(
            dataset_id=dataset.id,
            operator_name=dataset.organisation.name,
            short_description=dataset.live_revision.short_description,
            dataset_status=dataset.avl_feed_status,
            updated_time=dataset.modified,
            subscriber_email=developer.email,
        )


def send_avl_report_requires_resolution_notification(dataset: Dataset):
    revision = dataset.live_revision
    notifier.send_avl_report_requires_resolution(
        dataset_id=dataset.id,
        short_description=revision.short_description,
        operator_name=dataset.organisation.name,
        published_at=revision.published_at,
        feed_detail_link=dataset.feed_detail_url,
        contact_email=dataset.contact.email,
    )


def send_avl_flagged_with_compliance_issue(dataset: Dataset, status: str):
    for user in dataset.organisation.users.all():
        revision = dataset.live_revision
        notifier.send_avl_flagged_with_compliance_issue(
            dataset_id=dataset.id,
            short_description=revision.short_description,
            operator_name=dataset.organisation.name,
            published_at=revision.published_at,
            feed_detail_link=dataset.feed_detail_url,
            compliance=status,
            contact_email=user.email,
        )


def send_avl_flagged_with_major_issue(dataset: Dataset):
    for user in dataset.organisation.users.all():
        revision = dataset.live_revision
        notifier.send_avl_flagged_with_major_issue(
            dataset_id=dataset.id,
            short_description=revision.short_description,
            operator_name=dataset.organisation.name,
            published_at=revision.published_at,
            feed_detail_link=dataset.feed_detail_url,
            contact_email=user.email,
        )


def send_avl_schema_check_fail(dataset: Dataset):
    revision = dataset.live_revision
    notifier.send_avl_schema_check_fail(
        feed_name=revision.name,
        feed_id=dataset.id,
        short_description=revision.short_description,
        operator_name=dataset.organisation.name,
        published_at=revision.published_at,
        feed_detail_link=dataset.feed_detail_url,
        comments=revision.comment,
        contact_email=dataset.contact.email,
    )


def send_avl_compliance_status_changed(datafeed: AVLDataset, old_status: str):
    """
    Sends an AVL compliance status has changed notification to a data feeds
    key contact.
    """
    revision = datafeed.live_revision
    now = timezone.now()
    users = datafeed.organisation.users.select_related("settings")
    for user in users:
        if user.settings.daily_compliance_check_alert:
            notifier.send_avl_compliance_status_changed(
                feed_id=datafeed.id,
                short_description=revision.short_description,
                operator_name=datafeed.organisation.name,
                old_status=old_status,
                new_status=datafeed.avl_compliance,
                updated_at=now,
                feed_detail_link=datafeed.feed_detail_url,
                contact_email=user.email,
            )
