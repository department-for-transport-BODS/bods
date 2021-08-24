import pytest
from django.utils.timezone import now

from transit_odp.organisation import signals
from transit_odp.organisation.factories import DatasetFactory, OrganisationFactory
from transit_odp.organisation.receivers import (
    feed_monitor_change_detected_handler,
    feed_monitor_dataset_available_handler,
    feed_monitor_fail_final_try_handler,
    feed_monitor_fail_first_try_handler,
    revision_publish_handler,
)
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import AgentUserInviteFactory
from transit_odp.users.models import AgentUserInvite

pytestmark = pytest.mark.django_db
target_module = "transit_odp.organisation.receivers"

NOW = now()


def setup_dataset(user_factory, staff_account=AccountType.org_staff.value):
    organisation = OrganisationFactory()
    staff_user = user_factory.create(
        account_type=staff_account, organisations=[organisation]
    )
    dev_user = user_factory.create(account_type=AccountType.developer.developer)
    dev_user.settings.mute_all_dataset_notifications = False
    dev_user.settings.save()
    dataset = DatasetFactory(
        contact=staff_user,
        organisation=organisation,
        live_revision__url_link="http://testserver.test.test",
        live_revision__last_modified_user=staff_user,
        live_revision__published_by=staff_user,
        live_revision__first_expiring_service=NOW,
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
        # Test
        registered_functions = [
            r[1]() for r in signals.feed_monitor_fail_first_try.receivers
        ]

        # Assert
        assert feed_monitor_fail_first_try_handler in registered_functions

    def test_notify_feed_monitor_fail_first_try_is_called(
        self, user_factory, mailoutbox
    ):
        # Set up
        dataset = setup_dataset(user_factory)

        # Test
        feed_monitor_fail_first_try_handler(None, dataset=dataset)

        # Assert
        assert mailoutbox[-1].subject == (
            "[BODS] We cannot access the URL where your bus data is hosted "
            "– no action required"
        )


class TestMonitorFeedFailFinalTryHandler:
    def test_connected(self):
        # Test
        registered_functions = [
            r[1]() for r in signals.feed_monitor_fail_final_try.receivers
        ]

        # Assert
        assert feed_monitor_fail_final_try_handler in registered_functions

    def test_notify_feed_fail_final_try_is_called(self, user_factory, mailoutbox):
        # Set up
        dataset = setup_dataset(user_factory)

        # Test
        feed_monitor_fail_final_try_handler(None, dataset=dataset)

        # Assert
        assert (
            mailoutbox[-1].subject
            == "[BODS] Your bus data has expired due to inaccessibility"
        )


class TestMonitorFeedChangeDetectedHandler:
    def test_connected(self):
        # Test
        registered_functions = [
            r[1]() for r in signals.feed_monitor_change_detected.receivers
        ]

        # Assert
        assert feed_monitor_change_detected_handler in registered_functions

    @pytest.mark.parametrize(
        "account_type", (AccountType.org_staff.value, AccountType.agent_user.value)
    )
    def test_notify_feed_monitor_change_detected_is_called(
        self, account_type, user_factory, mailoutbox
    ):
        # Set up
        dataset = setup_dataset(user_factory, staff_account=account_type)

        # Test
        feed_monitor_change_detected_handler(None, dataset=dataset)

        # Assert
        emails = [mail.subject for mail in mailoutbox]
        assert "[BODS] Developer Data Changed" in emails
        assert (
            "[BODS] A change has been detected in your bus data – no action required"
            in emails
        )


class TestMonitorFeedAvailableHandler:
    def test_connected(self):
        # Test
        registered_functions = [
            r[1]() for r in signals.feed_monitor_dataset_available.receivers
        ]

        # Assert
        assert feed_monitor_dataset_available_handler in registered_functions

    def test_notify_feed_monitor_available_is_called(self, user_factory, mailoutbox):
        # Set up
        dataset = setup_dataset(user_factory)

        # Test
        feed_monitor_dataset_available_handler(None, dataset)

        # Assert
        assert (
            mailoutbox[-1].subject
            == "[BODS] Your bus data is accessible again – no action required"
        )


class TestRevisionPublishHandler:
    def test_connected(self):
        # Test
        registered_functions = [r[1]() for r in signals.revision_publish.receivers]

        # Assert
        assert revision_publish_handler in registered_functions

    @pytest.mark.parametrize(
        "account_type", (AccountType.org_staff.value, AccountType.agent_user.value)
    )
    def test_notify_feed_published_is_called(
        self, account_type, user_factory, mailoutbox
    ):
        # Set up
        dataset = setup_dataset(user_factory, staff_account=account_type)

        # Test
        revision_publish_handler(None, dataset)

        # Assert
        assert mailoutbox[-1].subject == "[BODS] Data set published"
