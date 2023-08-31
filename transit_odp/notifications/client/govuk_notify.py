import logging
from typing import Dict

from django.conf import settings
from django.template.loader import render_to_string
from notifications_python_client.notifications import NotificationsAPIClient

from transit_odp.notifications.client.base import NotificationBase
from transit_odp.notifications.constants import TEMPLATE_LOOKUP

logger = logging.getLogger(__name__)


class GovUKNotifyEmail(NotificationBase):
    def __init__(self):
        super().__init__()
        api_key = settings.GOV_NOTIFY_API_KEY
        self.generic_template_id = settings.GENERIC_TEMPLATE_ID
        self._notification_client = NotificationsAPIClient(api_key=api_key)

    def _send_mail(self, template: str, email: str, subject: str, **kwargs):
        template_id = self.templates.get(template, self.generic_template_id)
        if template_id == self.generic_template_id:
            # We want to eventually move all emails to the custom template
            # here we only need to define body and subject
            template = TEMPLATE_LOOKUP[template]
            body = render_to_string(template, kwargs)
            personalisation = {"body": body, "subject": subject}
        else:
            personalisation = kwargs

        try:
            self._notification_client.send_email_notification(
                email_address=email,
                template_id=template_id,
                personalisation=personalisation,
            )
        except Exception as e:
            name = template.lower()
            logger.error(
                f"[notify_{name}] has encountered an exception while sending "
                f"notification: {e}"
            )

    @property
    def templates(self) -> Dict[str, str]:
        # This is now effectively a list of all the templates that need to move over
        return {
            "INVITE_USER": "9f4b5fd5-625a-44fb-8b4d-b50e8a7e7fb1",
            "OPERATOR_DATA_DELETED": "1b0c8b4f-e2ec-4004-a1c3-74f16649efba",
            "OPERATOR_DELETER_DATA_DELETED": "f7a1c6bf-9e4c-4896-a106-109f71fe52b6",
            "OPERATOR_DATA_ENDPOINT_UNREACHABLE_NOW_EXPIRING": (
                "41a079e9-6a09-40bc-be81-4fbf2e9d3087"
            ),
            "OPERATOR_DATA_ENDPOINT_NOW_REACHABLE": (
                "cc4e4f8f-d75e-4360-ac7f-e8eec5e9d340"
            ),
            "OPERATOR_DATA_CHANGED": "0d64bbb3-2959-4670-871d-2077d8504f53",
            "AGENT_DATA_CHANGED": "9a6a7ac6-3f2c-4541-8fa8-5325ee05e151",
            "AGENT_INVITE_ACCEPTED": "d5ddb8c7-6ef0-42f3-9333-50aa28f2778f",
            "AGENT_INVITE_EXISTING_ACCOUNT": "ea06ebdf-f5ed-46ba-a094-ef42f2afe21a",
            "AGENT_INVITE_NEW_ACCOUNT": "8866bc7b-5684-45b7-85fb-c300fc939827",
            "AGENT_INVITE_REJECTED": "72b5178f-050c-411b-8d34-c91bde4d170c",
            "AGENT_LEAVES_ORGANISATION": "46719db6-98b6-4595-8f67-ecf5fbd5df8e",
            "AGENT_NOC_CHANGED": "b82b1df7-4e64-4117-b615-3ee789fa7ed1",
            "AGENT_REMOVED_BY_OPERATOR": "f1148060-86b4-4140-a852-c09ce973c0cf",
            "OPERATOR_AGENT_INVITE_ACCEPTED": "7e8013f4-e092-477a-8ff7-9f7183ad814c",
            "OPERATOR_AGENT_LEAVES_ORGANISATION": (
                "8466a24a-18b9-4b11-9512-9519a224d412"
            ),
            "OPERATOR_AGENT_REJECTED_INVITE": "b7edcd7f-5c86-4c6e-b085-c72efb487bc7",
            "OPERATOR_NOC_CHANGED": "ca32baf1-a420-4893-98e8-04bd5e85a9c4",
            "DATASET_NO_LONGER_COMPLIANT": "3093797a-a1fa-4a08-8dc0-b0bfda4e3e64",
        }
