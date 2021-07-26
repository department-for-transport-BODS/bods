from django.db.models import Q

from transit_odp.bods.interfaces.notifications import INotifications
from transit_odp.bods.interfaces.plugins import get_notifications
from transit_odp.organisation.constants import TimetableType
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


def send_feed_changed_notification(dataset: Dataset):

    if not dataset.contact.is_agent_user:
        notifier.send_data_endpoint_changed_notification(
            dataset_id=dataset.id,
            dataset_name=dataset.live_revision.name,
            short_description=dataset.live_revision.short_description,
            feed_detail_link=dataset.feed_detail_url,
            contact_email=dataset.contact.email,
        )

    agents = dataset.organisation.agentuserinvite_set.filter(
        status=AgentUserInvite.ACCEPTED
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

    is_muted = Q(settings__mute_all_dataset_notifications=True)
    for developer in dataset.subscribers.exclude(is_muted).order_by("id"):
        notifier.send_developer_data_endpoint_changed_notification(
            dataset_id=dataset.id,
            dataset_name=dataset.live_revision.name,
            contact_email=developer.email,
            operator_name=dataset.organisation.name,
            last_updated=dataset.live_revision.modified,
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
    if not dataset.contact.is_agent_user:
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
        status=AgentUserInvite.ACCEPTED
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


def send_endpoint_validation_error_notification(dataset):
    content_template = (
        "The following data set has failed to publish on the Bus Open Data Service "
        "due to validation errors{0}.\n\n"
        "Please check your data set below to ensure that the most up-to-date "
        "information is maintained on BODS."
    )
    timetable_modifier = " in the files as specified in the Validation report"

    if dataset.dataset_type == TimetableType:
        content = content_template.format(timetable_modifier)
    else:
        content = content_template.format("")

    revision = dataset.revisions.get_draft().first()
    if revision is None:
        return

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
            content=content,
            short_description=revision.short_description,
            operator_name=dataset.organisation.name,
            published_at=live_revisions_published_date,
            comments=revision.comment,
            feed_detail_link=revision.draft_url,
            contact_email=dataset.contact.email,
        )
    else:
        notifier.send_data_endpoint_validation_error_notification(
            dataset_id=dataset.id,
            dataset_name=revision.name,
            content=content,
            short_description=revision.short_description,
            published_at=live_revisions_published_date,
            comments=revision.comment,
            feed_detail_link=revision.draft_url,
            contact_email=dataset.contact.email,
        )


def send_report_available_notifications(revision: DatasetRevision):
    contact = revision.dataset.contact
    if contact.is_agent_user:
        notifier.send_agent_reports_are_available_notification(
            dataset_id=revision.dataset_id,
            dataset_name=revision.name,
            operator_name=revision.dataset.organisation.name,
            short_description=revision.short_description,
            comments=revision.comment,
            draft_link=revision.draft_url,
            contact_email=contact.email,
        )
    else:
        notifier.send_reports_are_available_notification(
            dataset_id=revision.dataset_id,
            dataset_name=revision.name,
            short_description=revision.short_description,
            comments=revision.comment,
            draft_link=revision.draft_url,
            contact_email=contact.email,
        )
