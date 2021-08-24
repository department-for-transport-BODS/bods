import datetime
from typing import Optional, Protocol

from transit_odp.organisation.constants import AVLFeedStatus


class INotifications(Protocol):
    """
    Sends notifications
    """

    def send_data_endpoint_changed_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        feed_detail_link: str,
        contact_email: str,
    ):
        """Sends notification to Publisher that their remote TxC dataset has changed

        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            contact_email: email address of datasets key contact
        """
        ...

    def send_developer_data_endpoint_changed_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        contact_email: str,
        operator_name: str,
        last_updated: datetime.datetime,
    ):
        """Sends notification to Developer that their subscribed TxC dataset has
        changed"""
        ...

    def send_agent_data_endpoint_changed_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        feed_detail_link: str,
        operator_name: str,
        contact_email: str,
    ):
        """Sends notification to agents that their subscribed TxC dataset has
        changed

        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            operator_name: name of the operator that published the dataset
            contact_email: email address of agent working on behalf of organisation
        """
        ...

    def send_data_endpoint_unreachable_notification(
        self, dataset_id: int, dataset_name: str, contact_email: str
    ):
        """Sends notification to Publisher that their remote TxC dataset is
        unreachable"""
        ...

    def send_data_endpoint_reachable_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        contact_email: str,
    ):
        """Sends notification to operator that their previously unreachable
        url is now reachable"""
        ...

    def send_data_endpoint_unreachable_expiring_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        feed_detail_link: str,
        remote_url: str,
        contact_email: str,
    ):
        """Sends notification to Publisher that their unreachable TxC dataset is
        about to expire
        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            remote_url: url of remote server hosting dataset
            contact_email: email address of datasets key contact
        """
        ...

    def send_data_endpoint_deleted_deleter_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        contact_email: str,
    ):
        """Sends confirmation notification to Publisher that deleted the
        Publication/Draft"""
        ...

    def send_data_endpoint_deleted_updater_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        contact_email: str,
        last_updated: datetime.datetime,
    ):
        """Sends deleted dataset notification to last updated user"""
        ...

    def send_data_endpoint_deactivated_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        contact_email: str,
        published_at: datetime.datetime,
        expired_at: datetime.datetime,
    ):
        """Sends notification to Publisher that Publication has been deactivated"""
        ...

    def send_developer_data_endpoint_expired_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        contact_email: str,
        published_at: datetime.datetime,
        expired_at: Optional[datetime.datetime],
    ):
        """Sends notification to Developer that Publication has expired"""
        ...

    def send_agent_data_endpoint_deactivated_notification(
        self,
        dataset_id: int,
        dataset_name: int,
        contact_email: str,
        operator_name: str,
        short_description: str,
        published_at: datetime.datetime,
        expired_at: datetime.datetime,
    ):
        """Sends notification to agent that Publication has been deactivated"""
        ...

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
        """Sends notification to Publisher that the Publication has published.
        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            published_at: date and time of publish
            comments: any comments on the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            contact_email: email address of datasets key contact
            with_pti_violations: use template warning of PTI violations
        """
        ...

    def send_agent_data_endpoint_publish_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        published_at: datetime.datetime,
        comments: str,
        feed_detail_link: str,
        operator_name: str,
        contact_email: str,
        with_pti_violations: bool = False,
    ):
        """
        Sends notification to Agent Publisher that the Publication has published

        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            published_at: date and time of publish
            comments: any comments on the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            operator_name: name of the operator that published the dataset
            contact_email: email address of agent working on behalf of organisation
            with_pti_violations: use template warning of PTI violations

        Returns: None
        """
        ...

    def send_data_endpoint_validation_error_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        content: str,
        short_description: str,
        published_at: datetime.datetime,
        comments: str,
        feed_detail_link: str,
        contact_email: str,
    ):
        """Sends notification to Publisher that the Publication has validation errors
        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            published_at: date and time of publish
            comments: any comments on the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            contact_email: email address of agent working on behalf of organisation
        """
        ...

    def send_agent_data_endpoint_validation_error_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        content: str,
        short_description: str,
        published_at: datetime.datetime,
        operator_name: str,
        comments: str,
        feed_detail_link: str,
        contact_email: str,
    ):
        """Sends notification to Agent that the Publication has validation errors
        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            published_at: date and time of publish
            operator_name: name of the operator that published the dataset
            comments: any comments on the revision
            feed_detail_link: link to the feed-detail or revision-publish page
            contact_email: email address of agent working on behalf of organisation
        """
        ...

    def send_feedback_notification(
        self,
        publication_id: int,
        dataset_name: str,
        contact_email: str,
        feedback: str,
        developer_email: Optional[str] = None,
    ):
        """Sends notification to Publisher with feedback from (anonymous) user"""
        ...

    def send_invite_accepted_notification(
        self, inviter_email: str, invitee_email: str, organisation_name: str
    ):
        """Sends notification to Publisher that team member accepted invite"""
        ...

    def send_password_reset_notification(self, contact_email: str, reset_link: str):
        """Sends notification to User for password reset"""
        ...

    def send_invitation_notification(
        self, contact_email: str, organisation_name: str, invite_url: str
    ):
        """Sends invitation notification to User"""
        ...

    def send_verify_email_address_notification(
        self, contact_email: str, verify_link: str
    ):
        """Sends account verification notification to User"""
        ...

    def send_avl_feed_down_publisher_notification(
        self,
        publication_id: int,
        dataset_name: str,
        dataset_id: int,
        contact_email: str,
    ):
        """
        Sends a notification to Publisher informing them their AVLFeed has gone down

        The notification is sent to `contact_email`.

        Args:
            publication_id: The ID of the publication
            dataset_id: The ID of the dataset
            dataset_name: The name of the publication
            contact_email: The email of the recipient

        Returns: None

        """
        ...

    def send_avl_feed_subscriber_notification(
        self,
        publication_id: int,
        operator_name: str,
        dataset_status: AVLFeedStatus,
        updated_time: datetime.datetime,
        subscriber_email: str,
    ):
        """
        Sends a notification to Subscriber informing status of their subscribed feeds

        The notification is sent to `subscriber_email`.

        Args:
            publication_id: The ID of the publication
            operator_name: The name of the operator
            dataset_status: The status of the publication
            updated_time: The updated date time of the publication
            subscriber_email: The email of the recipient

        Returns: None

        """
        ...

    def send_agent_invite_accepted_notification(
        self, operator_name: str, agent_email: str
    ):
        """
        Sends a notification to agent confirming they have accepted invitation

        The notification is sent to `agent`.

        Args:
            operator_name: The name of the operator
            agent_email: The email of the recipient

        Returns: None

        """
        ...

    def send_agent_invite_existing_account_notification(
        self, operator_name: str, agent_email: str
    ):
        """
        Sends an invite to join BODS to agent with existing account

        The notification is sent to `agent`.

        Args:
            operator_name: The name of the operator
            agent_email: The email of the recipient

        Returns: None

        """
        ...

    def send_agent_invite_no_account_notification(
        self, contact_email: str, organisation_name: str, invite_url: str
    ):
        """
        Sends an invite to join BODS to agent with existing account

        The notification is sent to `agent`.

        Args:
            contact_email: The email of the recipient
            organisation_name: The name of the operator
            invite_url: link to my user registration page

        Returns: None

        """
        ...

    def send_agent_invite_rejected_notification(
        self,
        operator_name: str,
        agent_email: str,
    ):
        """
        Sends a notification to agent confirming they have rejected an invitation

        The notification is sent to `agent`.

        Args:
            operator_name: The name of the operator
            agent_email: The email of the recipient

        Returns: None

        """
        ...

    def send_agent_leaves_organisation_notification(
        self,
        operator_name: str,
        agent_email: str,
    ):
        """
        Sends a notification to agent confirming they have left an operator

        The notification is sent to `agent`.

        Args:
            operator_name: The name of the operator
            agent_email: The email of the recipient

        Returns: None

        """
        ...

    def send_agent_noc_changed_notification(
        self,
        operator_name: str,
        agent_email: str,
    ):
        """
        Sends a notification to agent confirming the NOC has changed

        The notification is sent to `agent`.

        Args:
            operator_name: The name of the operator
            agent_email: The email of the recipient

        Returns: None

        """
        ...

    def send_agent_operator_removes_agent_notification(
        self, operator_name: str, agent_email: str
    ):
        """
        Sends a notification to agent informing them that operator has removed them

        The notification is sent to `agent`.

        Args:
            operator_name: The name of the operator
            agent_email: The email of the recipient

        Returns: None

        """
        ...

    def send_operator_agent_accepted_invite_notification(
        self, agent_organisation: str, agent_inviter: str
    ):
        """
        Sends a notification to operator informing them that agent has accepted the
        invite

        The notification is sent to the `operator`.

        Args:
            agent_organisation: The name of the agents organisation
            agent_inviter: The email of the recipient

        Returns: None

        """
        ...

    def send_operator_agent_leaves_notification(
        self,
        agent_organisation: str,
        agent_inviter: str,
    ):
        """
        Sends a notification to operator informing them that agent has left the
        organisation

        The notification is sent to the `operator`.

        Args:
            agent_organisation: The name of the agents organisation
            agent_inviter: The email of the recipient

        Returns: None

        """
        ...

    def send_operator_agent_rejected_invite_notification(
        self,
        agent_organisation: str,
        agent_inviter: str,
    ):
        """
        Sends a notification to operator informing them that agent has rejected the
        invite

        The notification is sent to the `operator`.

        Args:
            agent_organisation: The name of the agents organisation
            agent_inviter: The email of the recipient

        Returns: None

        """
        ...

    def send_operator_agent_removed_notification(
        self,
        agent_organisation: str,
        agent_inviter: str,
    ):
        """
        Sends a notification to operator informing them that they has removed the
        agent

        The notification is sent to the `operator`.

        Args:
            agent_organisation: The name of the agents organisation
            agent_inviter: The email of the recipient

        Returns: None

        """
        ...

    def send_operator_noc_changed_notification(self, contact: str):
        """
        Sends a notification to operators key contact that the NOC has changed

        The notification is sent to the `operator`.

        Args:
            contact: The email of the recipient

        Returns: None

        """
        ...

    def send_reports_are_available_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        published_at: Optional[datetime.datetime],
        comments: str,
        draft_link: str,
        contact_email: str,
    ):
        """Sends notification to Publisher that reports are now available.
        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            published_at: datetime of when dateset was published
            comments: any comments on the revision
            draft_link: link to the revisions draft review page
            contact_email: email address of datasets key contact
        """
        ...

    def send_agent_reports_are_available_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        comments: str,
        operator_name: str,
        published_at: Optional[datetime.datetime],
        draft_link: str,
        contact_email: str,
    ):
        """Sends notification to agent that reports are now available.
        Args:
            dataset_id: id (primary key) of the dataset model
            dataset_name: name assigned to the revision
            short_description: short description of the revision
            comments: any comments on the revision
            operator_name: name of the operator that published the dataset
            published_at: datetime of when dateset was published
            draft_link: link to the revisions draft review page
            contact_email: email address of datasets key contact
        """
        ...

    def send_custom_email(
        self,
        template: str,
        subject: str,
        body: str,
        contact_email: str,
    ):
        """Sends a custom email.
        Args:
            template: template id for email
            subject: subject of email
            body: body of email
            contact_email: email address of datasets key contact
        """
        ...
