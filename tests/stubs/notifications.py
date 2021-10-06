import datetime
from collections import defaultdict
from typing import Dict, List, Optional

from pydantic import validate_arguments

from transit_odp.bods.interfaces.notifications import INotifications


class FakeNotifications(INotifications):
    sent: Dict[str, List[str]]

    def __init__(self):
        self.sent = defaultdict(list)

    @validate_arguments
    def send_data_endpoint_changed_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        feed_detail_link: str,
        contact_email: str,
    ):

        template = "OPERATOR_DATA_CHANGED"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_developer_data_endpoint_changed_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        contact_email: str,
        operator_name: str,
        last_updated: datetime.datetime,
    ):
        template = "DEVELOPER_DATA_CHANGED"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_data_endpoint_unreachable_notification(
        self, dataset_id: int, dataset_name: str, contact_email: str
    ):
        template = "OPERATOR_DATA_ENDPOINT_UNREACHABLE"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_data_endpoint_reachable_notification(
        self, publication_id: int, dataset_name: str, contact_email: str
    ):
        template = "OPERATOR_DATA_ENDPOINT_NOW_REACHABLE"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_data_endpoint_unreachable_expiring_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        feed_detail_link: str,
        remote_url: str,
        contact_email: str,
    ):
        template = "OPERATOR_DATA_ENDPOINT_UNREACHABLE_NOW_EXPIRING"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_data_endpoint_deleted_deleter_notification(
        self, dataset_id: int, dataset_name: str, contact_email: str
    ):
        template = "OPERATOR_DELETER_DATA_DELETED"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_data_endpoint_deleted_updater_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        contact_email: str,
        last_updated: datetime.datetime,
    ):
        template = "OPERATOR_DATA_DELETED"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_data_endpoint_deactivated_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description,
        contact_email: str,
        published_at: datetime.datetime,
        expired_at: datetime.datetime,
    ):
        template = "OPERATOR_EXPIRED_NOTIFICATION"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_developer_data_endpoint_expired_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        contact_email: str,
        published_at: datetime.datetime,
        expired_at: datetime.datetime,
    ):
        template = "OPERATOR_EXPIRED_NOTIFICATION"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_data_endpoint_publish_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        published_at: datetime.datetime,
        comments: str,
        feed_detail_link: str,
        contact_email: str,
        with_pti_violations: bool = False,
    ):
        template = "OPERATOR_PUBLISH_LIVE"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_data_endpoint_validation_error_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        dataset_type: int,
        published_at: datetime.datetime,
        comments: str,
        feed_detail_link: str,
        contact_email: str,
        with_pti_violations: bool = False,
    ):
        template = "OPERATOR_PUBLISH_ERROR"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_feedback_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        feed_detail_link: str,
        contact_email: str,
        feedback: str,
        developer_email: Optional[str] = None,
    ):
        # TODO - rethink this...
        # If unit tests need to test different variations of each email,
        # e.g. like in this case
        # where we want to test the email was went anonymously, then we should either:
        #    * just use a Mock to test the method call_args directly, or
        #    * append an object to the internal to better describe the sent notification
        # The second option gives us the benefits of using a fake rather than a mock,
        # i.e. we can
        # test the state of FakeNotifications rather than testing a specific
        # interaction with some method
        prefix = ""
        if developer_email is None:
            prefix = "-anonymous"
        template = f"OPERATOR_FEEDBACK{prefix}"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_invite_accepted_notification(
        self, inviter_email: str, invitee_email: str, organisation_name: str
    ):
        template = "OPERATOR_INVITE_ACCEPTED"
        self.sent[inviter_email].append(template)

    @validate_arguments
    def send_password_reset_notification(self, contact_email: str, reset_link: str):
        template = "PASSWORD_RESET"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_invitation_notification(
        self, contact_email: str, organisation_name: str, invite_url: str
    ):
        template = "INVITE_USER"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_verify_email_address_notification(
        self, contact_email: str, verify_link: str
    ):
        template = "VERIFY_EMAIL_ADDRESS"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_avl_feed_down_publisher_notification(
        self,
        dataset_name: str,
        dataset_id: int,
        short_description: str,
        contact_email: str,
    ):
        template = "OPERATOR_AVL_ENDPOINT_UNREACHABLE"
        self.sent[contact_email].append(template)

    @validate_arguments
    def send_avl_feed_subscriber_notification(
        self,
        dataset_id: int,
        operator_name: str,
        short_description: str,
        dataset_status: str,
        updated_time: datetime.datetime,
        subscriber_email: str,
    ):
        template = "DEVELOPER_AVL_FEED_STATUS_NOTIFICATION"
        self.sent[subscriber_email].append(template)
