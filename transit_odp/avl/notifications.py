from datetime import datetime, timezone

from transit_odp.avl.proxies import AVLDataset
from transit_odp.notifications import get_notifications
from transit_odp.notifications.client import INotifications
from transit_odp.organisation.models import Dataset

notifier: INotifications = get_notifications()


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
    now = datetime.now(tz=timezone.utc)
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
