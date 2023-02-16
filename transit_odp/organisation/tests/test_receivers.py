import pytest
from django.utils import timezone

from transit_odp.organisation import signals
from transit_odp.organisation.factories import DatasetFactory, OrganisationFactory
from transit_odp.organisation.receivers import (
    feed_monitor_dataset_available_handler,
    feed_monitor_fail_final_try_handler,
    feed_monitor_fail_first_try_handler,
    revision_publish_handler,
)
from transit_odp.users.constants import AgentUserType, DeveloperType, OrgStaffType
from transit_odp.users.factories import AgentUserInviteFactory
from transit_odp.users.models import AgentUserInvite

pytestmark = pytest.mark.django_db
target_module = "transit_odp.organisation.receivers"


def setup_dataset(user_factory, staff_account=OrgStaffType):
    organisation = OrganisationFactory()
    staff_user = user_factory.create(
        account_type=staff_account, organisations=[organisation]
    )
    dev_user = user_factory.create(account_type=DeveloperType)
    dev_user.settings.mute_all_dataset_notifications = False
    dev_user.settings.save()
    now = timezone.now()
    dataset = DatasetFactory(
        contact=staff_user,
        organisation=organisation,
        live_revision__url_link="http://testserver.test.test",
        live_revision__last_modified_user=staff_user,
        live_revision__published_by=staff_user,
        live_revision__first_expiring_service=now,
    )
    dataset.subscribers.add(dev_user)
    dataset.save()
    if staff_user.is_agent_user:
        AgentUserInviteFactory.create(
            agent=staff_user, organisation=organisation, status=AgentUserInvite.ACCEPTED
        )

    return dataset


class TestMonitorFeedFailFirstTryHandler:
    def test_connected(self):
        registered_functions = [
            r[1]() for r in signals.feed_monitor_fail_first_try.receivers
        ]
        assert feed_monitor_fail_first_try_handler in registered_functions

    def test_notify_feed_monitor_fail_first_try_is_called(
        self, user_factory, mailoutbox
    ):
        dataset = setup_dataset(user_factory)
        feed_monitor_fail_first_try_handler(None, dataset=dataset)
        expected_subject = (
            "We cannot access the URL where your bus data is hosted "
            "– no action required"
        )
        assert mailoutbox[-1].subject == expected_subject


class TestMonitorFeedFailFinalTryHandler:
    def test_connected(self):
        registered_functions = [
            r[1]() for r in signals.feed_monitor_fail_final_try.receivers
        ]
        assert feed_monitor_fail_final_try_handler in registered_functions

    def test_notify_feed_fail_final_try_is_called(self, user_factory, mailoutbox):
        """
        GIVEN A organisation user with a published remote dataset and developer
        subscribed to that dataset.
        WHEN `feed_monitor_fail_final_try_handler` is called.
        THEN Two emails should be sent, one to the publisher and one to the
        developer/consumer.
        """
        dataset = setup_dataset(user_factory)
        feed_monitor_fail_final_try_handler(None, dataset=dataset)

        assert len(mailoutbox) == 2
        publisher_mailbox, consumer_mailbox = mailoutbox

        publisher_subject = "Your bus data has expired due to inaccessibility"
        assert publisher_mailbox.subject == publisher_subject

        consumer_subject = "Data set status changed"
        assert consumer_mailbox.subject == consumer_subject


class TestMonitorFeedAvailableHandler:
    def test_connected(self):
        registered_functions = [
            r[1]() for r in signals.feed_monitor_dataset_available.receivers
        ]
        assert feed_monitor_dataset_available_handler in registered_functions

    def test_notify_feed_monitor_available_is_called(self, user_factory, mailoutbox):
        dataset = setup_dataset(user_factory)
        feed_monitor_dataset_available_handler(None, dataset)
        expected_subject = "Your bus data is accessible again – no action required"
        assert mailoutbox[-1].subject == expected_subject


class TestRevisionPublishHandler:
    def test_connected(self):
        registered_functions = [r[1]() for r in signals.revision_publish.receivers]
        assert revision_publish_handler in registered_functions

    @pytest.mark.parametrize("account_type", (OrgStaffType, AgentUserType))
    def test_notify_feed_published_is_called(
        self, account_type, user_factory, mailoutbox
    ):
        dataset = setup_dataset(user_factory, staff_account=account_type)
        revision_publish_handler(None, dataset)
        assert len(mailoutbox) == 2
        publisher, developer = mailoutbox
        assert publisher.subject == "Data set published"
        assert developer.subject == "Data set status changed"
