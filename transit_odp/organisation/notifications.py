from django.db.models import Q
from django.utils import timezone

from transit_odp.notifications import get_notifications
from transit_odp.notifications.client import INotifications
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.users.models import AgentUserInvite

notifier: INotifications = get_notifications()


def send_feed_monitor_fail_first_try_notification(dataset: Dataset):
    notifier.send_data_endpoint_unreachable_notification(
        dataset_id=dataset.id,
        dataset_name=dataset.live_revision.name,
        contact_email=dataset.contact.email,
    )


def send_feed_monitor_fail_final_try_notification(dataset: Dataset):
    notifier.send_data_endpoint_unreachable_expiring_notification(
        dataset_id=dataset.id,
        dataset_name=dataset.live_revision.name,
        short_description=dataset.live_revision.short_description,
        feed_detail_link=dataset.feed_detail_url,
        remote_url=dataset.live_revision.url_link,
        contact_email=dataset.contact.email,
    )

    now = timezone.now()
    subscribers = dataset.subscribers.filter(is_active=True)
    for subscriber in subscribers:
        notifier.send_developer_data_endpoint_changed_notification(
            dataset_id=dataset.id,
            dataset_name=dataset.live_revision.name,
            contact_email=subscriber.email,
            operator_name=dataset.organisation.name,
            last_updated=now,
        )


def send_feed_changed_notification(dataset: Dataset):

    if not dataset.contact.is_agent_user and dataset.contact.is_active:
        notifier.send_data_endpoint_changed_notification(
            dataset_id=dataset.id,
            dataset_name=dataset.live_revision.name,
            short_description=dataset.live_revision.short_description,
            feed_detail_link=dataset.feed_detail_url,
            contact_email=dataset.contact.email,
        )

    agents = dataset.organisation.agentuserinvite_set.filter(
        status=AgentUserInvite.ACCEPTED, agent__is_active=True
    )
    for agent in agents:
        notifier.send_agent_data_endpoint_changed_notification(
            dataset_id=dataset.id,
            dataset_name=dataset.live_revision.name,
            short_description=dataset.live_revision.short_description,
            feed_detail_link=dataset.feed_detail_url,
            operator_name=dataset.organisation.name,
            contact_email=agent.email,
        )


def send_endpoint_available_notification(dataset: Dataset):
    notifier.send_data_endpoint_reachable_notification(
        dataset_id=dataset.id,
        dataset_name=dataset.live_revision.name,
        short_description=dataset.live_revision.short_description,
        contact_email=dataset.contact.email,
    )


def send_revision_published_notification(dataset: Dataset):

    has_pti_violations = not dataset.live_revision.is_pti_compliant()
    if not dataset.contact.is_agent_user and dataset.contact.is_active:
        notifier.send_data_endpoint_publish_notification(
            dataset_id=dataset.id,
            dataset_name=dataset.live_revision.name,
            short_description=dataset.live_revision.short_description,
            published_at=dataset.live_revision.published_at,
            comments=dataset.live_revision.comment,
            feed_detail_link=dataset.feed_detail_url,
            contact_email=dataset.contact.email,
            with_pti_violations=has_pti_violations,
        )

    agents = dataset.organisation.agentuserinvite_set.filter(
        status=AgentUserInvite.ACCEPTED, agent__is_active=True
    )
    for agent in agents:
        notifier.send_agent_data_endpoint_publish_notification(
            dataset_id=dataset.id,
            dataset_name=dataset.live_revision.name,
            short_description=dataset.live_revision.short_description,
            published_at=dataset.live_revision.published_at,
            comments=dataset.live_revision.comment,
            feed_detail_link=dataset.feed_detail_url,
            operator_name=dataset.organisation.name,
            contact_email=agent.email,
            with_pti_violations=has_pti_violations,
        )

    is_muted = Q(settings__mute_all_dataset_notifications=True)
    for developer in (
        dataset.subscribers.exclude(is_muted).filter(is_active=True).order_by("id")
    ):
        # For new datasets there will be no subscribers so this wont get sent.
        # It will only email developers when new revisions are published
        notifier.send_developer_data_endpoint_changed_notification(
            dataset_id=dataset.id,
            dataset_name=dataset.live_revision.name,
            contact_email=developer.email,
            operator_name=dataset.organisation.name,
            last_updated=dataset.live_revision.published_at,
        )


def send_endpoint_validation_error_notification(dataset):
    revision = dataset.revisions.get_draft().first()
    if revision is None:
        return

    has_pti_errors = not revision.is_pti_compliant()
    # If published_at has any meaning at all its when was the datasets
    # live revision published
    if dataset.live_revision:
        live_revisions_published_date = dataset.live_revision.published_at
    else:
        live_revisions_published_date = None

    if dataset.contact.is_agent_user:
        notifier.send_agent_data_endpoint_validation_error_notification(
            dataset_id=dataset.id,
            dataset_name=revision.name,
            short_description=revision.short_description,
            dataset_type=dataset.dataset_type,
            operator_name=dataset.organisation.name,
            published_at=live_revisions_published_date,
            comments=revision.comment,
            feed_detail_link=revision.draft_url,
            contact_email=dataset.contact.email,
            with_pti_violations=has_pti_errors,
        )
    else:
        notifier.send_data_endpoint_validation_error_notification(
            dataset_id=dataset.id,
            dataset_name=revision.name,
            short_description=revision.short_description,
            dataset_type=dataset.dataset_type,
            published_at=live_revisions_published_date,
            comments=revision.comment,
            feed_detail_link=revision.draft_url,
            contact_email=dataset.contact.email,
            with_pti_violations=has_pti_errors,
        )


def send_report_available_notifications(revision: DatasetRevision):
    contact = revision.dataset.contact
    dataset = revision.dataset

    if dataset.live_revision:
        live_revisions_published_date = dataset.live_revision.published_at
    else:
        live_revisions_published_date = None

    if contact.is_agent_user:
        notifier.send_agent_reports_are_available_notification(
            dataset_id=revision.dataset_id,
            dataset_name=revision.name,
            operator_name=revision.dataset.organisation.name,
            short_description=revision.short_description,
            comments=revision.comment,
            draft_link=revision.draft_url,
            published_at=live_revisions_published_date,
            contact_email=contact.email,
        )
    else:
        notifier.send_reports_are_available_notification(
            dataset_id=revision.dataset_id,
            dataset_name=revision.name,
            short_description=revision.short_description,
            comments=revision.comment,
            draft_link=revision.draft_url,
            published_at=live_revisions_published_date,
            contact_email=contact.email,
        )
