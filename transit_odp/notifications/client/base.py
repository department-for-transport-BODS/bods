import datetime
import logging
from abc import abstractmethod
from typing import Optional

from django.conf import settings
from django.utils import timezone
from django_hosts.resolvers import reverse
from pydantic import validate_arguments

import config.hosts
from transit_odp.bods.interfaces.notifications import INotifications
from transit_odp.common.utils.convert_datetime import (
    localize_datetime_and_convert_to_string,
)
from transit_odp.organisation.constants import AVLFeedDown

logger = logging.getLogger(__name__)
ACCOUNT_SETTINGS_VIEW = "users:settings"
MY_ACCOUNT_HOME = "users:home"
OPERATOR_GUIDANCE = "guidance:support-bus_operators"
DATA_QUALITY_SECTION = "dataquality"


class NotificationBase(INotifications):
    @property
    @abstractmethod
    def templates(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def _send_mail(self, template: str, email: str, subject: str, **kwargs):
        raise NotImplementedError

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
        logger.debug(
            f"[notify_{template.lower()}] notifying last modified user that dataset"
            f"<id={dataset_id} has changed>"
        )
        subject = "A change has been detected in your bus data – no action required"
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            link=feed_detail_link,
        )

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
        logger.debug(
            f"[notify_{template.lower()}] notifying all subscribers "
            f"that dataset<id={dataset_id} has changed>"
        )
        subject = "Data set status changed"
        last_update_date = localize_datetime_and_convert_to_string(last_updated)
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            operator_name=operator_name,
            updated_time=last_update_date,
        )

    @validate_arguments
    def send_agent_data_endpoint_changed_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        feed_detail_link: str,
        operator_name: str,
        contact_email: str,
    ):
        template = "AGENT_DATA_CHANGED"
        subject = "A change has been detected in your bus data – no action required"
        logger.debug(
            f"[notify_{template.lower()}] notifying agent {contact_email} "
            f"that dataset<id={dataset_id} has changed>"
        )
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            organisation=operator_name,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            link=feed_detail_link,
        )

    @validate_arguments
    def send_data_endpoint_unreachable_notification(
        self, dataset_id: int, dataset_name: str, contact_email: str
    ):
        template = "OPERATOR_DATA_ENDPOINT_UNREACHABLE"
        logger.debug(
            f"[notify_{template.lower()}] notifying last modified"
            f" user that dataset<id={dataset_id} is unreachable>"
        )
        subject = (
            "We cannot access the URL where your bus data is hosted"
            " – no action required"
        )

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
        )

    @validate_arguments
    def send_data_endpoint_reachable_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        contact_email: str,
    ):
        template = "OPERATOR_DATA_ENDPOINT_NOW_REACHABLE"
        subject = "Your bus data is accessible again – no action required"
        logger.debug(
            f"[notify_{template.lower()}] notifying last modified"
            f" user that dataset<id={dataset_id} is now reachable>"
        )
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
        )

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
        logger.debug(
            f"[notify_{template.lower()}] notifying last modified user "
            f"rthat the unreachable dataset<id={dataset_id} is now expired>"
        )
        subject = "Your bus data has expired due to inaccessibility"
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_id=dataset_id,
            feed_name=dataset_name,
            feed_short_description=short_description,
            link=feed_detail_link,
            data_set_url=remote_url,
        )

    @validate_arguments
    def send_data_endpoint_deleted_deleter_notification(
        self, dataset_id: int, dataset_name: str, contact_email: str
    ):
        template = "OPERATOR_DELETER_DATA_DELETED"
        logger.debug(
            f"[notify_{template.lower()}] notifying deleting user that dataset"
            f"<id={dataset_id} has been deleted>"
        )
        subject = "You deleted an unpublished data set – no action required"
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
        )

    @validate_arguments
    def send_data_endpoint_deleted_updater_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        contact_email: str,
        last_updated: datetime.datetime,
    ):
        template = "OPERATOR_DATA_DELETED"
        logger.debug(
            f"[notify_{template.lower()}] notifying last modified user that"
            f" dataset<id={dataset_id} has been deleted>"
        )
        subject = (
            "A data set you updated has been deleted from the Bus Open Data "
            "Service – no action required"
        )
        last_update_date = localize_datetime_and_convert_to_string(last_updated)
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
            last_update_date=last_update_date,
        )

    @validate_arguments
    def send_data_endpoint_deactivated_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        contact_email: str,
        published_at: datetime.datetime,
        expired_at: Optional[datetime.datetime],
    ):
        template = "OPERATOR_EXPIRED_NOTIFICATION"
        subject = "Published data set has been deactivated"
        logger.debug(
            f"[notify_{template.lower()}] notifying last modified user dataset expired "
            f"for Dataset<id={dataset_id}>"
        )

        expires_on = (
            localize_datetime_and_convert_to_string(expired_at)
            if expired_at is not None
            else "N/A"
        )
        published_on = localize_datetime_and_convert_to_string(published_at)
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            published_time=published_on,
            expiry_time=expires_on,
        )

    @validate_arguments
    def send_developer_data_endpoint_expired_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        contact_email: str,
        published_at: datetime.datetime,
        expired_at: Optional[datetime.datetime],
    ):
        template = "OPERATOR_EXPIRED_NOTIFICATION"
        subject = "Published data set has been deactivated"
        logger.debug(
            f"[notify_{template.lower()}] notifying all subscribers that dataset"
            f"<id={dataset_id} has expired>"
        )
        expires_on = (
            localize_datetime_and_convert_to_string(expired_at)
            if expired_at is not None
            else "N/A"
        )
        published_on = localize_datetime_and_convert_to_string(published_at)
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            published_time=published_on,
            expiry_time=expires_on,
        )

    @validate_arguments
    def send_agent_data_endpoint_deactivated_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        contact_email: str,
        operator_name: str,
        short_description: str,
        published_at: datetime.datetime,
        expired_at: Optional[datetime.datetime],
    ):
        template = "AGENT_EXPIRED_NOTIFICATION"
        subject = "Published data set has been deactivated"
        logger.debug(
            f"[notify_{template.lower()}] notifying {contact_email} dataset expired "
            f"for Dataset<id={dataset_id}>"
        )

        expires_on = (
            localize_datetime_and_convert_to_string(expired_at)
            if expired_at is not None
            else "N/A"
        )
        published_on = localize_datetime_and_convert_to_string(published_at)
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            organisation=operator_name,
            feed_id=dataset_id,
            feed_name=dataset_name,
            feed_short_description=short_description,
            published_time=published_on,
            expiry_time=expires_on,
        )

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

        if with_pti_violations:
            template = "OPERATOR_PUBLISH_LIVE_WITH_PTI_VIOLATIONS"
            subject = "Action required – PTI validation report requires resolution"

        else:
            template = "OPERATOR_PUBLISH_LIVE"
            subject = "Data set published"

        logger.debug(
            f"[notify_{template.lower()}] notifying organisation staff/admin dataset "
            f"Dataset<id={dataset_id}> successfully published"
        )
        published_on = localize_datetime_and_convert_to_string(published_at)
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            published_time=published_on,
            comments=comments,
            link=feed_detail_link,
            pti_enforced_date=settings.PTI_ENFORCED_DATE,
        )

    @validate_arguments
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

        if with_pti_violations:
            template = "AGENT_PUBLISH_LIVE_WITH_PTI_VIOLATIONS"
            subject = "Action required – PTI validation report requires resolution"

        else:
            template = "AGENT_PUBLISH_LIVE"
            subject = "Data set published"

        logger.debug(
            f"[notify_{template.lower()}] notifying agent {contact_email} dataset "
            f"Dataset<id={dataset_id}> successfully published"
        )
        published_on = localize_datetime_and_convert_to_string(published_at)
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            organisation=operator_name,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            published_time=published_on,
            comments=comments,
            link=feed_detail_link,
            pti_enforced_date=settings.PTI_ENFORCED_DATE,
        )

    @validate_arguments
    def send_data_endpoint_validation_error_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        dataset_type: int,
        published_at: Optional[datetime.datetime],
        comments: str,
        feed_detail_link: str,
        contact_email: str,
        with_pti_violations: bool = False,
    ):
        template = "OPERATOR_PUBLISH_ERROR"
        logger.debug(
            f"[notify_{template.lower()}] notifying organisation staff/admin dataset "
            f"Dataset<id={dataset_id}> has entered error state due to validation"
        )
        subject = "Error publishing data set"
        published_on = (
            "Not published"
            if published_at is None
            else localize_datetime_and_convert_to_string(published_at)
        )
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            published_time=published_on,
            comments=comments,
            link=feed_detail_link,
            dataset_type=dataset_type,
            with_pti_violations=with_pti_violations,
        )

    @validate_arguments
    def send_agent_data_endpoint_validation_error_notification(
        self,
        dataset_id: int,
        dataset_name: str,
        short_description: str,
        dataset_type: int,
        published_at: Optional[datetime.datetime],
        operator_name: str,
        comments: str,
        feed_detail_link: str,
        contact_email: str,
        with_pti_violations: bool = False,
    ):
        template = "AGENT_PUBLISH_ERROR"
        logger.debug(
            f"[notify_{template.lower()}] notifying organisation agent dataset "
            f"Dataset<id={dataset_id}> has entered error state due to validation"
        )
        subject = "Error publishing data set"

        if published_at is None:
            published_on = "Not published"
        else:
            published_on = localize_datetime_and_convert_to_string(published_at)

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
            organisation=operator_name,
            feed_short_description=short_description,
            published_time=published_on,
            comments=comments,
            link=feed_detail_link,
            dataset_type=dataset_type,
            with_pti_violations=with_pti_violations,
        )

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
        template = "OPERATOR_FEEDBACK"
        subject = "You have feedback on your data"
        logger.debug(
            f"[notify_{template.lower()}] sending feedback to publisher about dataset "
            f"Dataset<id={dataset_id}>"
        )
        if developer_email is None:
            developer_email = "Anonymous"
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_id=dataset_id,
            feed_name=dataset_name,
            link=feed_detail_link,
            user_email=developer_email,
            feedback=feedback,
        )

    @validate_arguments
    def send_invite_accepted_notification(
        self, inviter_email: str, invitee_email: str, organisation_name: str
    ):
        template = "OPERATOR_INVITE_ACCEPTED"
        logger.debug(
            f"[notify_{template.lower()}] notifying inviter {inviter_email} "
            f"that user {invitee_email} has accepted invitation"
        )
        subject = "Your team member has accepted your invitation"
        self._send_mail(
            template,
            inviter_email,
            subject=subject,
            organisation=organisation_name,
            name=invitee_email,
        )

    @validate_arguments
    def send_password_reset_notification(self, contact_email: str, reset_link: str):
        template = "PASSWORD_RESET"
        subject = "Change your password on the Bus Open Data Service"
        logger.debug(f"sending password reset to {contact_email}")
        self._send_mail(template, contact_email, subject=subject, reset_link=reset_link)

    @validate_arguments
    def send_password_change_notification(self, contact_email: str):
        template = "PASSWORD_CHANGED"
        subject = "You have changed your password on the Bus Open Data Service"
        logger.debug(f"sending password changed to {contact_email}")
        self._send_mail(template, contact_email, subject=subject)

    @validate_arguments
    def send_invitation_notification(
        self, contact_email: str, organisation_name: str, invite_url: str
    ):
        template = "INVITE_USER"
        logger.debug(f"[notify_{template.lower()}] inviting new user to join bods")
        subject = "You have been invited to publish bus data"
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            organisation=organisation_name,
            signup_link=invite_url,
        )

    @validate_arguments
    def send_verify_email_address_notification(
        self, contact_email: str, verify_link: str
    ):
        template = "VERIFY_EMAIL_ADDRESS"
        subject = "Confirm your email address"
        logger.debug(
            f"[notify_{template.lower()}] sending verify email address notification"
        )
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            verify_link=verify_link,
        )

    @validate_arguments
    def send_avl_feed_down_publisher_notification(
        self,
        dataset_name: str,
        dataset_id: int,
        short_description: str,
        contact_email: str,
    ):
        template = "OPERATOR_AVL_ENDPOINT_UNREACHABLE"
        account_settings_link = reverse(
            ACCOUNT_SETTINGS_VIEW, host=config.hosts.PUBLISH_HOST
        )
        logger.debug(
            f"[notify_{template.lower()}] notifying last modified user that dataset"
            f"<id={dataset_id} is unreachable>"
        )
        subject = (
            f"AVL Feed {dataset_id} is no longer sending data to the "
            "Bus Open Data Service"
        )
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            data_feed_name=dataset_name,
            data_feed_id=dataset_id,
            feed_short_description=short_description,
            settings_link=account_settings_link,
        )

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
        subject = "Data feed status changed"
        logger.debug(
            f"[notify_{template.lower()}] notifying subscribers about status of dataset"
            f"<id={dataset_id} >"
        )
        feed_status = (
            "No vehicle activity" if dataset_status == AVLFeedDown else "Published"
        )

        last_updated = localize_datetime_and_convert_to_string(updated_time)

        self._send_mail(
            template,
            subscriber_email,
            subject=subject,
            feed_id=dataset_id,
            operator_name=operator_name,
            feed_short_description=short_description,
            status=feed_status,
            updated_time=last_updated,
        )

    @validate_arguments
    def send_avl_report_requires_resolution(
        self,
        dataset_id: int,
        short_description: str,
        operator_name: str,
        published_at: datetime.datetime,
        feed_detail_link: str,
        contact_email: str,
    ):
        template = "AVL_REPORT_REQUIRES_RESOLUTION"
        subject = "Action required - SIRI-VM validation report requires resolution"
        guidance = reverse(OPERATOR_GUIDANCE, host=config.hosts.PUBLISH_HOST)
        guidance = f"{guidance}?section={DATA_QUALITY_SECTION}"

        logger.debug(f"[notify_{template.lower()}] AVL report requires resolution")
        deadline = published_at + datetime.timedelta(days=7)
        published_time = localize_datetime_and_convert_to_string(published_at)

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_id=dataset_id,
            operator_name=operator_name,
            feed_short_description=short_description,
            published_time=published_time,
            deadline=deadline,
            link=feed_detail_link,
            guidance=guidance,
        )

    @validate_arguments
    def send_avl_flagged_with_compliance_issue(
        self,
        dataset_id: int,
        short_description: str,
        operator_name: str,
        published_at: datetime.datetime,
        feed_detail_link: str,
        compliance: str,
        contact_email: str,
    ):
        template = "AVL_FLAGGED_WITH_COMPLIANCE"
        subject = f"SIRI-VM validation: Your feed is flagged to public as {compliance}"
        guidance = reverse(OPERATOR_GUIDANCE, host=config.hosts.PUBLISH_HOST)
        guidance = f"{guidance}?section={DATA_QUALITY_SECTION}"

        logger.debug(
            f"[notify_{template.lower()}] "
            f"AVL dataset {dataset_id} flagged: {compliance}"
        )
        published_time = localize_datetime_and_convert_to_string(published_at)

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_id=dataset_id,
            operator_name=operator_name,
            feed_short_description=short_description,
            published_time=published_time,
            compliance=compliance,
            link=feed_detail_link,
            guidance=guidance,
        )

    @validate_arguments
    def send_avl_flagged_with_major_issue(
        self,
        dataset_id: int,
        short_description: str,
        operator_name: str,
        published_at: datetime.datetime,
        feed_detail_link: str,
        contact_email: str,
    ):
        template = "AVL_FLAGGED_WITH_MAJOR_ISSUE"
        subject = "Action required - SIRI-VM validation report requires resolution"
        guidance = reverse(OPERATOR_GUIDANCE, host=config.hosts.PUBLISH_HOST)
        guidance = f"{guidance}?section={DATA_QUALITY_SECTION}"

        logger.debug(
            f"[notify_{template.lower()}] "
            f"AVL dataset {dataset_id} flagged with major issue"
        )
        published_time = localize_datetime_and_convert_to_string(published_at)

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_id=dataset_id,
            operator_name=operator_name,
            feed_short_description=short_description,
            published_time=published_time,
            link=feed_detail_link,
            guidance=guidance,
        )

    @validate_arguments
    def send_avl_schema_check_fail(
        self,
        feed_name: str,
        feed_id: int,
        short_description: str,
        operator_name: str,
        published_at: datetime.datetime,
        comments: str,
        feed_detail_link: str,
        contact_email: str,
    ):
        template = "AVL_SCHEMA_CHECK_FAILED"
        subject = "Error publishing data feed"

        logger.debug(
            f"[notify_{template.lower()}] "
            f"AVL dataset {feed_id} has failed the schema check"
        )
        published_time = localize_datetime_and_convert_to_string(published_at)

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=feed_name,
            feed_id=feed_id,
            operator_name=operator_name,
            feed_short_description=short_description,
            published_time=published_time,
            comments=comments,
            link=feed_detail_link,
        )

    @validate_arguments
    def send_avl_compliance_status_changed(
        self,
        feed_id: int,
        short_description: str,
        operator_name: str,
        new_status: str,
        old_status: str,
        updated_at: datetime.datetime,
        feed_detail_link: str,
        contact_email: str,
    ):

        template = "AVL_COMPLIANCE_STATUS_CHANGED"
        subject = f"SIRI-VM compliance status changed to {new_status}"
        settings_link = reverse("users:settings", host=config.hosts.PUBLISH_HOST)

        logger.debug(
            f"[notify_{template.lower()}] "
            f"AVL dataset {feed_id} has failed the schema check"
        )
        updated_at = localize_datetime_and_convert_to_string(updated_at)
        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_id=feed_id,
            short_description=short_description,
            operator_name=operator_name,
            new_status=new_status,
            old_status=old_status,
            updated_at=updated_at,
            link=feed_detail_link,
            settings_link=settings_link,
        )

    @validate_arguments
    def send_agent_invite_accepted_notification(
        self, operator_name: str, agent_email: str
    ):
        template = "AGENT_INVITE_ACCEPTED"
        subject = (
            f"You have accepted the request to be an agent on behalf of {operator_name}"
        )
        logger.debug(
            f"[notify_{template.lower()}] confirming agent ({agent_email} has accepted "
            f"invite to {operator_name}>"
        )

        self._send_mail(
            template, agent_email, subject=subject, organisation=operator_name
        )

    @validate_arguments
    def send_agent_invite_existing_account_notification(
        self, operator_name: str, agent_email: str
    ):
        template = "AGENT_INVITE_EXISTING_ACCOUNT"
        subject = (
            f"{operator_name} has invited you to act as an agent on behalf of them"
        )
        agent_invite_link = reverse(MY_ACCOUNT_HOME, host=config.hosts.PUBLISH_HOST)
        logger.debug(
            f"[notify_{template.lower()}] inviting agent ({agent_email} to "
            f"{operator_name}>"
        )

        self._send_mail(
            template,
            agent_email,
            subject=subject,
            organisation=operator_name,
            agent_invite_link=agent_invite_link,
        )

    @validate_arguments
    def send_agent_invite_no_account_notification(
        self, contact_email: str, organisation_name: str, invite_url: str
    ):
        template = "AGENT_INVITE_NEW_ACCOUNT"
        subject = (
            f"{organisation_name} has invited you to act as an agent on behalf of them"
        )
        logger.debug(
            f"[notify_{template.lower()}] inviting agent ({contact_email} to "
            f"{organisation_name}>"
        )

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            organisation=organisation_name,
            signup_link=invite_url,
        )

    @validate_arguments
    def send_agent_invite_rejected_notification(
        self,
        operator_name: str,
        agent_email: str,
    ):
        template = "AGENT_INVITE_REJECTED"
        subject = (
            f"You have rejected the request to become an agent on behalf of "
            f"{operator_name}"
        )
        logger.debug(
            f"[notify_{template.lower()}] confirming agent ({agent_email} has rejected "
            f"invite to {operator_name}>"
        )

        self._send_mail(
            template, agent_email, subject=subject, organisation=operator_name
        )

    @validate_arguments
    def send_agent_leaves_organisation_notification(
        self,
        operator_name: str,
        agent_email: str,
    ):
        template = "AGENT_LEAVES_ORGANISATION"
        subject = f"You have stopped acting as an agent on behalf of {operator_name}"
        logger.debug(
            f"[notify_{template.lower()}] confirming agent ({agent_email} has left "
            f"{operator_name}>"
        )

        self._send_mail(
            template, agent_email, subject=subject, organisation=operator_name
        )

    @validate_arguments
    def send_agent_noc_changed_notification(
        self,
        operator_name: str,
        agent_email: str,
    ):
        template = "AGENT_NOC_CHANGED"
        subject = f"{operator_name}'s National Operator Code (NOC) has been amended"
        logger.debug(
            f"[notify_{template.lower()}] notifying ({agent_email} that "
            f"{operator_name} NOC has changed>"
        )

        self._send_mail(
            template, agent_email, subject=subject, organisation=operator_name
        )

    @validate_arguments
    def send_agent_operator_removes_agent_notification(
        self, operator_name: str, agent_email: str
    ):
        template = "AGENT_REMOVED_BY_OPERATOR"
        subject = f"{operator_name} has removed you as their agent"
        logger.debug(
            f"[notify_{template.lower()}] notifying ({agent_email} that "
            f"{operator_name} removed them>"
        )

        self._send_mail(
            template, agent_email, subject=subject, organisation=operator_name
        )

    @validate_arguments
    def send_operator_agent_accepted_invite_notification(
        self, agent_organisation: str, agent_inviter: str
    ):
        template = "OPERATOR_AGENT_INVITE_ACCEPTED"
        subject = f"Agent {agent_organisation} has accepted your invitation"
        logger.debug(
            f"[notify_{template.lower()}] notifying inviter {agent_inviter} "
            f"that user {agent_organisation} has accepted invitation"
        )
        self._send_mail(
            template,
            agent_inviter,
            subject=subject,
            agent_organisation=agent_organisation,
        )

    @validate_arguments
    def send_operator_agent_leaves_notification(
        self,
        agent_organisation: str,
        agent_inviter: str,
    ):
        template = "OPERATOR_AGENT_LEAVES_ORGANISATION"
        subject = f"{agent_organisation} has terminated their role as an agent"
        logger.debug(
            f"[notify_{template.lower()}] notifying inviter {agent_inviter} "
            f"that user {agent_organisation} has left the organisation"
        )
        self._send_mail(
            template,
            agent_inviter,
            subject=subject,
            agent_organisation=agent_organisation,
        )

    @validate_arguments
    def send_operator_agent_rejected_invite_notification(
        self,
        agent_organisation: str,
        agent_inviter: str,
    ):
        template = "OPERATOR_AGENT_REJECTED_INVITE"
        subject = f"{agent_organisation} has rejected your request to act as an agent"
        logger.debug(
            f"[notify_{template.lower()}] notifying inviter {agent_inviter} "
            f"that user {agent_organisation} has rejected invitation"
        )
        self._send_mail(
            template,
            agent_inviter,
            subject=subject,
            agent_organisation=agent_organisation,
        )

    @validate_arguments
    def send_operator_agent_removed_notification(
        self,
        agent_organisation: str,
        agent_inviter: str,
    ):
        template = "OPERATOR_AGENT_REMOVED"
        subject = f"You have removed {agent_organisation} as your agent"
        logger.debug(
            f"[notify_{template.lower()}] notifying inviter {agent_inviter} "
            f"that user {agent_organisation} has been removed by operator"
        )
        self._send_mail(
            template,
            agent_inviter,
            subject=subject,
            agent_organisation=agent_organisation,
        )

    @validate_arguments
    def send_operator_noc_changed_notification(self, contact: str):
        template = "OPERATOR_NOC_CHANGED"
        subject = "Your organisation’s National Operator Code (NOC) has been amended"
        logger.debug(
            f"[notify_{template.lower()}] notifying {contact} that NOC has changed>"
        )

        self._send_mail(
            template,
            contact,
            subject=subject,
        )

    @validate_arguments
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

        template = "REPORTS_AVAILABLE"
        subject = (
            "Action required – PTI validation report requires resolution "
            "(if applicable)"
        )
        published_on = (
            "Not published"
            if published_at is None
            else localize_datetime_and_convert_to_string(published_at)
        )
        logger.debug(
            f"[notify_{template.lower()}] notifying organisation staff/admin dataset "
            f"Dataset<id={dataset_id}> that reports now available"
        )

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            comments=comments,
            published_time=published_on,
            link=draft_link,
            pti_enforced_date=settings.PTI_ENFORCED_DATE,
            pti_enforced=settings.PTI_ENFORCED_DATE.date() < timezone.localdate(),
        )

    @validate_arguments
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
        template = "AGENT_REPORTS_AVAILABLE"
        subject = (
            "Action required – PTI validation report requires resolution "
            "(if applicable)"
        )
        logger.debug(
            f"[notify_{template.lower()}] notifying agent"
            f"Dataset<id={dataset_id}> that reports now available"
        )
        published_on = (
            "Not published"
            if published_at is None
            else localize_datetime_and_convert_to_string(published_at)
        )

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            organisation=operator_name,
            feed_name=dataset_name,
            feed_id=dataset_id,
            feed_short_description=short_description,
            comments=comments,
            published_time=published_on,
            link=draft_link,
            pti_enforced_date=settings.PTI_ENFORCED_DATE,
            pti_enforced=settings.PTI_ENFORCED_DATE.date() < timezone.localdate(),
        )

    @validate_arguments
    def send_custom_email(
        self,
        template: str,
        subject: str,
        body: str,
        contact_email: str,
    ):
        logger.debug(f"sending custom email with template id: {template}")

        self._send_mail(
            template,
            contact_email,
            subject=subject,
            body=body,
        )
