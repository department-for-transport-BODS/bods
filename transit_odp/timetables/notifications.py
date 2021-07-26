from django.db.models import QuerySet

from transit_odp.bods.interfaces.notifications import INotifications
from transit_odp.bods.interfaces.plugins import get_notifications
from transit_odp.common.utils.convert_datetime import (
    localize_datetime_and_convert_to_string,
)
from transit_odp.organisation.models import Dataset

notifier: INotifications = get_notifications()


def send_data_no_longer_compliant_notification(
    contact: str, txc21datasets: "QuerySet[Dataset]"
):
    template = "DATASET_NO_LONGER_COMPLIANT"
    subject = "Your data set is no longer compliant"

    body_template = (
        "Data set: {name}\n"
        "Data set ID: {dataset_id}\n"
        "Short Description: {short_description}\n"
        "Published: {published}\n"
        "Link: {link}\n"
    )
    dataset_details = []
    for dataset in txc21datasets:
        details = body_template.format(
            name=dataset.live_revision.name,
            dataset_id=dataset.id,
            short_description=dataset.live_revision.short_description,
            published=localize_datetime_and_convert_to_string(
                dataset.live_revision.published_at
            ),
            link=dataset.live_revision.draft_url,
        )
        dataset_details.append(details)

    body = "\n".join(dataset_details)
    # Additional newline is appended to the end of body need to slice it off.
    notifier.send_custom_email(
        template=template, subject=subject, contact_email=contact, body=body[:-1]
    )
