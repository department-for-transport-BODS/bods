import pytest
from django.utils.timezone import now

from transit_odp.notifications.client import DjangoNotifier


class TestDjangoNotification:
    contact_email = "user@test.com"
    dataset_name = "test_dataset"
    organisation_name = "test_organisation"
    dataset_id = 1
    agent_contact_email = "agent@test.com"
    agent_inviter_email = "agent_inviter@test.com"
    agent_organisation = "agentsRus"
    short_description = "test dataset for these tests"
    feed_detail_link = "http://publish.bods.local:8000/org/1/dataset/timetable/"
    comments = "first publication"

    def test_send_data_endpoint_changed_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_data_endpoint_changed_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            short_description=self.short_description,
            feed_detail_link=self.feed_detail_link,
            contact_email=self.contact_email,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert (
            m.subject
            == "[BODS] A change has been detected in your bus data – no action required"
        )

    def test_data_endpoint_changed_developer(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_developer_data_endpoint_changed_notification(
            dataset_id=1,
            dataset_name=self.dataset_name,
            contact_email=self.contact_email,
            operator_name=self.organisation_name,
            last_updated=now(),
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}Developer Data Changed"

    def test_data_endpoint_unreachable(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_data_endpoint_unreachable_notification(
            dataset_id=1,
            dataset_name=self.dataset_name,
            contact_email=self.contact_email,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == (
            f"{settings.EMAIL_SUBJECT_PREFIX}We cannot access the URL where your "
            "bus data is hosted – no action required"
        )

    def test_send_data_endpoint_reachable_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_data_endpoint_reachable_notification(
            dataset_id=1,
            dataset_name=self.dataset_name,
            contact_email=self.contact_email,
            short_description=self.short_description,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == (
            f"{settings.EMAIL_SUBJECT_PREFIX}Your bus data is accessible again "
            f"– no action required"
        )

    def test_send_data_endpoint_unreachable_expiring_notification(
        self, mailoutbox, settings
    ):
        dataset_url = "https://www.example.com"
        client = DjangoNotifier()
        client.send_data_endpoint_unreachable_expiring_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            short_description=self.short_description,
            feed_detail_link=self.feed_detail_link,
            remote_url=dataset_url,
            contact_email=self.contact_email,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == (
            f"{settings.EMAIL_SUBJECT_PREFIX}Your bus data has expired due to "
            f"inaccessibility"
        )
        assert dataset_url in m.body

    def test_send_data_endpoint_deleted_confirmation_notification(
        self, mailoutbox, settings
    ):
        client = DjangoNotifier()
        client.send_data_endpoint_deleted_deleter_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            contact_email=self.contact_email,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == (
            f"{settings.EMAIL_SUBJECT_PREFIX}You deleted an unpublished data set"
            f" – no action required"
        )

    def test_send_data_endpoint_deleted_notify_updater(self, mailoutbox, settings):
        last_updated = now()
        client = DjangoNotifier()
        client.send_data_endpoint_deleted_updater_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            contact_email=self.contact_email,
            last_updated=last_updated,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == (
            f"{settings.EMAIL_SUBJECT_PREFIX}A data set you updated has been "
            "deleted from the Bus Open Data Service – no action required"
        )

    def test_send_data_endpoint_has_expired_notification(self, mailoutbox, settings):
        published_at = now()
        expired_at = now()

        client = DjangoNotifier()
        client.send_data_endpoint_deactivated_notification(
            dataset_id=1,
            dataset_name=self.dataset_name,
            contact_email=self.contact_email,
            short_description=self.short_description,
            published_at=published_at,
            expired_at=expired_at,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}Published data set has been deactivated"
        )

    def test_send_developer_data_endpoint_expired_notification(
        self, mailoutbox, settings
    ):
        published_at = now()
        expired_at = now()

        client = DjangoNotifier()
        client.send_developer_data_endpoint_expired_notification(
            dataset_id=1,
            dataset_name=self.dataset_name,
            contact_email=self.contact_email,
            short_description=self.short_description,
            published_at=published_at,
            expired_at=expired_at,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}Published data set has been deactivated"
        )

    @pytest.mark.parametrize(
        "with_pti_observations, subject",
        [
            (False, "Data set published"),
            (True, "Action required – PTI validation report requires resolution"),
        ],
    )
    def test_send_data_endpoint_published_notification(
        self, with_pti_observations, subject, mailoutbox, settings
    ):
        published_at = now()

        client = DjangoNotifier()
        client.send_data_endpoint_publish_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            short_description=self.short_description,
            published_at=published_at,
            comments=self.comments,
            feed_detail_link=self.feed_detail_link,
            contact_email=self.contact_email,
            with_pti_violations=with_pti_observations,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}{subject}"

    def test_send_data_endpoint_error_notification(self, mailoutbox, settings):
        published_at = now()

        client = DjangoNotifier()
        client.send_data_endpoint_validation_error_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            content="content",
            short_description=self.short_description,
            published_at=published_at,
            comments=self.comments,
            feed_detail_link=self.feed_detail_link,
            contact_email=self.contact_email,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}Error publishing data set"

    def test_send_data_endpoint_error_notification_agent(self, mailoutbox, settings):
        published_at = now()

        client = DjangoNotifier()
        client.send_agent_data_endpoint_validation_error_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            content="content",
            short_description=self.short_description,
            published_at=published_at,
            comments=self.comments,
            operator_name=self.agent_organisation,
            feed_detail_link=self.feed_detail_link,
            contact_email=self.agent_contact_email,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}Error publishing data set"

    @pytest.mark.parametrize(
        "developer_email",
        [None, "developer@gmail.com"],
        ids=["anonymous_feedback", "signed_feedback"],
    )
    def test_send_feedback_notification(self, developer_email, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_feedback_notification(
            publication_id=1,
            dataset_name=self.dataset_name,
            contact_email=self.contact_email,
            feedback="This is something that could be improved",
            developer_email=developer_email,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}Operator Feedback"

        anonymised = developer_email is None
        if anonymised:
            assert not ("developer@gmail.com" in m.body)
        else:
            assert developer_email in m.body

    def test_send_invite_accepted_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_invite_accepted_notification(
            inviter_email="admin@org.com",
            invitee_email="staff@org.com",
            organisation_name=self.organisation_name,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == ["admin@org.com"]
        assert m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}Operator Invite Accepted"

    def test_send_password_reset_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_password_reset_notification(
            contact_email=self.contact_email,
            reset_link="https://www.bods.com/invite_url/",
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}Password Reset"
        assert "https://www.bods.com/invite_url/" in m.body

    def test_send_invitation_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_invitation_notification(
            contact_email=self.contact_email,
            organisation_name=self.organisation_name,
            invite_url="https://www.bods.com/invite_url/",
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}Invite User"

    def test_send_verify_email_address_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_verify_email_address_notification(
            contact_email=self.contact_email,
            verify_link="https://www.bods.com/invite_url/",
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}Verify Email Address"

    def test_send_avl_feed_down_publisher_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_avl_feed_down_publisher_notification(
            publication_id=1,
            dataset_name=self.dataset_name,
            contact_email=self.contact_email,
            dataset_id=self.dataset_id,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}Operator Avl Endpoint Unreachable"
        )

    def test_send_agent_invite_accepted_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_agent_invite_accepted_notification(
            self.organisation_name, self.agent_contact_email
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}You have accepted the request to be an "
            f"agent on behalf of test_organisation"
        )

    def test_send_agent_invite_existing_account_notification(
        self, mailoutbox, settings
    ):
        client = DjangoNotifier()
        client.send_agent_invite_existing_account_notification(
            self.organisation_name, self.agent_contact_email
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}test_organisation has invited you to "
            f"act as an agent on behalf of them"
        )

    def test_send_agent_invite_no_account_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_agent_invite_no_account_notification(
            self.agent_contact_email, self.organisation_name, "www.signuphere.com"
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}test_organisation has invited you to "
            f"act as an agent on behalf of them"
        )

    def test_send_agent_invite_rejected_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_agent_invite_rejected_notification(
            self.organisation_name, self.agent_contact_email
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}You have rejected the request to "
            f"become an agent on behalf of test_organisation"
        )

    def test_send_agent_leaves_organisation_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_agent_leaves_organisation_notification(
            self.organisation_name, self.agent_contact_email
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}You have stopped acting as an agent on "
            f"behalf of test_organisation"
        )

    def test_send_agent_noc_changed_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_agent_noc_changed_notification(
            self.organisation_name, self.agent_contact_email
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}test_organisation's National Operator "
            f"Code (NOC) has been amended"
        )

    def test_send_agent_operator_removes_agent_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_agent_operator_removes_agent_notification(
            self.organisation_name, self.agent_contact_email
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}test_organisation has removed you as "
            f"their agent"
        )

    def test_send_operator_agent_accepted_invite_notification(
        self, mailoutbox, settings
    ):
        client = DjangoNotifier()
        client.send_operator_agent_accepted_invite_notification(
            self.agent_organisation, self.agent_inviter_email
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_inviter_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}Agent agentsRus has accepted your "
            f"invitation"
        )

    def test_send_operator_agent_leaves_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_operator_agent_leaves_notification(
            self.agent_organisation, self.agent_inviter_email
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_inviter_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}agentsRus has terminated their role as "
            f"an agent"
        )

    def test_send_operator_agent_rejected_invite_notification(
        self, mailoutbox, settings
    ):
        client = DjangoNotifier()
        client.send_operator_agent_rejected_invite_notification(
            self.agent_organisation, self.agent_inviter_email
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_inviter_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}agentsRus has rejected your request to "
            f"act as an agent"
        )

    def test_send_operator_agent_removed_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_operator_agent_removed_notification(
            self.agent_organisation, self.agent_inviter_email
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_inviter_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}You have removed agentsRus as your "
            f"agent"
        )

    def test_send_operator_noc_changed_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_operator_noc_changed_notification(self.contact_email)
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}Your organisation’s National Operator "
            f"Code (NOC) has been amended"
        )

    def test_send_agent_data_endpoint_changed_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_agent_data_endpoint_changed_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            short_description=self.short_description,
            feed_detail_link=self.feed_detail_link,
            operator_name=self.organisation_name,
            contact_email=self.agent_contact_email,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}A change has been detected in your bus "
            f"data – no action required"
        )

    def test_send_agent_data_endpoint_expired_notification(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_agent_data_endpoint_deactivated_notification(
            self.dataset_id,
            self.dataset_name,
            self.contact_email,
            self.organisation_name,
            self.short_description,
            now(),
            now(),
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert (
            m.subject
            == f"{settings.EMAIL_SUBJECT_PREFIX}Published data set has been deactivated"
        )

    @pytest.mark.parametrize(
        "with_pti_observations, subject",
        [
            (False, "Data set published"),
            (True, "Action required – PTI validation report requires resolution"),
        ],
    )
    def test_send_agent_data_endpoint_published_notification(
        self, mailoutbox, settings, with_pti_observations, subject
    ):
        client = DjangoNotifier()
        client.send_agent_data_endpoint_publish_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            short_description=self.short_description,
            published_at=now(),
            comments=self.comments,
            feed_detail_link=self.feed_detail_link,
            operator_name=self.organisation_name,
            contact_email=self.agent_contact_email,
            with_pti_violations=with_pti_observations,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}{subject}"

    def test_reports_now_available(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_reports_are_available_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            short_description=self.short_description,
            comments=self.comments,
            draft_link=self.feed_detail_link,
            published_at=None,
            contact_email=self.contact_email,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.contact_email]
        assert (
            m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}Action required – "
            f"PTI validation report requires resolution (if applicable)"
        )

    def test_reports_now_available_to_agent(self, mailoutbox, settings):
        client = DjangoNotifier()
        client.send_agent_reports_are_available_notification(
            dataset_id=self.dataset_id,
            dataset_name=self.dataset_name,
            short_description=self.short_description,
            comments=self.comments,
            operator_name=self.agent_organisation,
            draft_link=self.feed_detail_link,
            published_at=None,
            contact_email=self.agent_contact_email,
        )
        [m] = mailoutbox
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [self.agent_contact_email]
        assert (
            m.subject == f"{settings.EMAIL_SUBJECT_PREFIX}Action required – "
            f"PTI validation report requires resolution (if applicable)"
        )
