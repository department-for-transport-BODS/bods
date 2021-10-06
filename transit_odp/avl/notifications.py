from transit_odp.bods.interfaces.notifications import INotifications
from transit_odp.bods.interfaces.plugins import get_notifications
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
