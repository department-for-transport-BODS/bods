from typing import Dict

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from transit_odp.notifications.client.base import NotificationBase


class DjangoNotifier(NotificationBase):
    def __init__(self):
        super().__init__()
        self.subject_prefix = getattr(settings, "EMAIL_SUBJECT_PREFIX", "[BODS]")
        self.from_email = getattr(
            settings, "DEFAULT_FROM_EMAIL", "Bus Open Data Service <noreply@bods.com>"
        )

    def _send_mail(self, template: str, email: str, **kwargs):
        """
        :param template: path to template
        :param email: address to send email to
        :param subject: email subject, defaulted to key of template dict
        :param kwargs: the remaining kwargs are render template variables
        :return:
        """
        template_path = self.templates[template]
        default_subject = template.title().replace("_", " ")
        subject = kwargs.pop("subject", default_subject)
        subject = f"{self.subject_prefix}{subject}"
        body = render_to_string(template_path, kwargs)

        send_mail(subject, body, self.from_email, [email])

    @property
    def templates(self) -> Dict[str, str]:
        return {
            "VERIFY_EMAIL_ADDRESS": "notifications/verify_email_address.txt",
            "INVITE_USER": "notifications/invite_user.txt",
            "PASSWORD_RESET": "notifications/password_reset.txt",
            "OPERATOR_INVITE_ACCEPTED": "notifications/invite_accepted.txt",
            "OPERATOR_FEEDBACK": "notifications/leave_feedback.txt",
            "OPERATOR_DATA_DELETED": (
                "notifications/"
                "data_end_point_deleted_notifying_last_updated_user.txt"
            ),
            "OPERATOR_DELETER_DATA_DELETED": (
                "notifications/data_end_point_deleted_notifying_deleting_user.txt"
            ),
            "OPERATOR_DATA_ENDPOINT_UNREACHABLE_NOW_EXPIRING": (
                "notifications/" "data_end_pount_unreachable_expiring.txt"
            ),
            "OPERATOR_DATA_ENDPOINT_NOW_REACHABLE": (
                "notifications/" "data_end_point_now_reachable.txt"
            ),
            "OPERATOR_DATA_ENDPOINT_UNREACHABLE": (
                "notifications/data_end_point_unreachable.txt"
            ),
            "OPERATOR_DATA_CHANGED": "notifications/data_end_point_changed.txt",
            "DEVELOPER_DATA_CHANGED": (
                "notifications/data_end_point_changed_developer.txt"
            ),
            "AGENT_DATA_CHANGED": "notifications/data_end_point_changed_agent.txt",
            "OPERATOR_PUBLISH_LIVE": "notifications/data_end_point_published.txt",
            "OPERATOR_PUBLISH_LIVE_WITH_PTI_VIOLATIONS": (
                "notifications/data_end_point_published_with_pti_violations.txt"
            ),
            "AGENT_PUBLISH_LIVE": "notifications/data_end_point_published_agent.txt",
            "AGENT_PUBLISH_LIVE_WITH_PTI_VIOLATIONS": (
                "notifications/data_end_point_published_with_pti_violations_agent.txt"
            ),
            "OPERATOR_PUBLISH_ERROR": (
                "notifications/data_end_point_error_publishing.txt"
            ),
            "AGENT_PUBLISH_ERROR": (
                "notifications/data_end_point_error_publishing_agent.txt"
            ),
            "OPERATOR_EXPIRED_NOTIFICATION": (
                "notifications/data_end_point_expired.txt"
            ),
            "AGENT_EXPIRED_NOTIFICATION": (
                "notifications/data_end_point_expired_agent.txt"
            ),
            "OPERATOR_AVL_ENDPOINT_UNREACHABLE": (
                "notifications/avl_end_point_unreachable.txt"
            ),
            "DEVELOPER_AVL_FEED_STATUS_NOTIFICATION": (
                "notifications/avl_feed_changed_developer.txt"
            ),
            "AGENT_INVITE_ACCEPTED": "notifications/agent_invite_accepted.txt",
            "AGENT_INVITE_EXISTING_ACCOUNT": (
                "notifications/agent_invite_existing_account.txt"
            ),
            "AGENT_INVITE_NEW_ACCOUNT": "notifications/agent_invite_no_account.txt",
            "AGENT_INVITE_REJECTED": "notifications/agent_invite_rejected.txt",
            "AGENT_LEAVES_ORGANISATION": "notifications/agent_leaves_operator.txt",
            "AGENT_NOC_CHANGED": "notifications/agent_noc_changed.txt",
            "AGENT_REMOVED_BY_OPERATOR": (
                "notifications/agent_operator_removes_agent.txt"
            ),
            "OPERATOR_AGENT_INVITE_ACCEPTED": (
                "notifications/operator_agent_accepted_invite.txt"
            ),
            "OPERATOR_AGENT_LEAVES_ORGANISATION": (
                "notifications/operator_agent_leaves.txt"
            ),
            "OPERATOR_AGENT_REJECTED_INVITE": (
                "notifications/operator_agent_rejected_invite.txt"
            ),
            "OPERATOR_AGENT_REMOVED": "notifications/operator_agent_removed.txt",
            "OPERATOR_NOC_CHANGED": "notifications/operator_noc_changed.txt",
            "REPORTS_AVAILABLE": "notifications/reports_are_available.txt",
            "AGENT_REPORTS_AVAILABLE": "notifications/reports_are_available_agent.txt",
        }
