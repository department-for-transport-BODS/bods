from unittest.mock import call

import pytest
from allauth.account.models import EmailAddress, EmailConfirmation
from django_hosts.resolvers import get_host, reverse

import config.hosts
from transit_odp.common.utils.convert_datetime import (
    localize_datetime_and_convert_to_string,
)
from transit_odp.notifications.client.govuk_notify import GovUKNotifyEmail
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.pipelines.factories import DatasetETLErrorFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import InvitationFactory, UserFactory

target_module = "transit_odp.notifications.client.govuk_notify"

pytestmark = pytest.mark.django_db


# TODO - update these tests as proper integration tests against GOVUK.Notify


def setup_mocking(mocker):
    templates_return_value = {
        "OPERATOR_DATA_DELETED": "1",
        "OPERATOR_DELETER_DATA_DELETED": "2",
        "OPERATOR_DATA_ENDPOINT_UNREACHABLE_NOW_EXPIRING": "3",
        "OPERATOR_DATA_ENDPOINT_NOW_REACHABLE": "4",
        "OPERATOR_DATA_ENDPOINT_UNREACHABLE": "5",
        "OPERATOR_DATA_CHANGED": "6",
        "DEVELOPER_DATA_CHANGED": "7",
        "OPERATOR_PUBLISH_LIVE": "8",
        "OPERATOR_PUBLISH_ERROR": "9",
        "OPERATOR_EXPIRED_NOTIFICATION": "11",
        "VERIFY_EMAIL_ADDRESS": "12",
        "INVITE_USER": "13",
        "PASSWORD_RESET": "14",
        "OPERATOR_INVITE_ACCEPTED": "15",
        "OPERATOR_FEEDBACK": "16",
    }
    mocker.patch.object(
        GovUKNotifyEmail,
        "templates",
        new_callable=mocker.PropertyMock,
        return_value=templates_return_value,
    )
    client = GovUKNotifyEmail()
    mocker.patch.object(client._notification_client, "send_email_notification")

    return client


def setup_simple_revisions(user):
    """Simple setup that creates one dataset with one live revision"""
    return DatasetFactory(
        contact=user,
        live_revision__published_by=user,
        live_revision__last_modified_user=user,
        live_revision__url_link="http://broken.test",
    )


def setup_complex_revisions(user):
    """Complex setup that creates one dataset with 5 revisions
    including 2 users plus celery"""
    user1 = UserFactory(account_type=AccountType.org_admin.value)
    # create first revision indirectly
    dataset = DatasetFactory(
        contact=user,
        live_revision__published_by=user1,
        live_revision__last_modified_user=user1,
        live_revision__url_link="http://broken.test",
    )
    # Note this creates a live revision

    # Simulate celery job running once
    DatasetRevisionFactory.create(
        dataset=dataset,
        published_by=None,
        last_modified_user=None,
        url_link="http://broken.test",
    )
    # Simulate celery job running twice:
    # Note, not using create batch because I want signals to run as normal
    DatasetRevisionFactory.create(
        dataset=dataset,
        published_by=None,
        last_modified_user=None,
        url_link="http://broken.test",
    )
    # Simulate revision changed by actual person
    DatasetRevisionFactory.create(
        dataset=dataset,
        published_by=user,
        last_modified_user=user,
        url_link="http://broken.test",
    )
    # And for good measure simulate celery running one more time
    DatasetRevisionFactory.create(
        dataset=dataset,
        published_by=None,
        last_modified_user=None,
        url_link="http://broken.test",
    )
    return dataset


@pytest.fixture(params=[setup_simple_revisions, setup_complex_revisions])
def datasets(request, user_factory):
    # This is what im trying to do:
    # https://docs.pytest.org/en/latest/fixture.html#fixture-parametrize
    setup_function = request.param
    org_user = user_factory(account_type=AccountType.org_admin.value)
    org_user.settings.notify_invitation_accepted = True
    org_user.settings.save()
    dataset = setup_function(org_user)
    return dataset, org_user


@pytest.mark.skip
def test_data_endpoint_changed(mocker, datasets):
    # Set up
    client = setup_mocking(mocker)
    dataset, org_user = datasets

    # Test
    client.send_data_endpoint_changed_notification(dataset)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=org_user.email,
        template_id="6",
        personalisation={"data_set_name": dataset.live_revision.name},
    )


@pytest.mark.skip
def test_data_endpoint_changed_developer(mocker, user_factory):
    # Set up
    client = setup_mocking(mocker)

    # create Feed with operator and FeedSubscriber
    org_user = user_factory(account_type=AccountType.org_admin.value)
    bob = user_factory(name="bob", account_type=AccountType.developer.value)
    charlie = user_factory(name="charlie", account_type=AccountType.developer.value)
    dataset = DatasetFactory(
        subscribers=[bob, charlie],
        live_revision__last_modified_user=org_user,
        live_revision__published_by=org_user,
    )
    updated_time = localize_datetime_and_convert_to_string(
        dataset.live_revision.modified
    )

    # Test
    client.send_developer_data_endpoint_changed_notification(dataset)

    # Assert
    bob_call = call(
        email_address=bob.email,
        template_id="7",
        personalisation={
            "feed_name": dataset.live_revision.name,
            "operator_name": dataset.organisation.name,
            "updated_time": updated_time,
        },
    )

    charlie_call = call(
        email_address=charlie.email,
        template_id="7",
        personalisation={
            "feed_name": dataset.live_revision.name,
            "operator_name": dataset.organisation.name,
            "updated_time": updated_time,
        },
    )

    client._notification_client.send_email_notification.assert_has_calls(
        [bob_call, charlie_call]
    )


@pytest.mark.skip
def test_data_endpoint_unreachable(mocker, datasets):
    # Set up
    client = setup_mocking(mocker)
    dataset, org_user = datasets

    # Test
    client.send_data_endpoint_unreachable_notification(dataset)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=org_user.email,
        template_id="5",
        personalisation={"data_set_name": dataset.live_revision.name},
    )


@pytest.mark.skip
def test_data_endpoint_unreachable_now_working(mocker, datasets):
    # Set up
    client = setup_mocking(mocker)
    dataset, org_user = datasets

    # Test
    client.send_data_endpoint_reachable_notification(dataset)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=org_user.email,
        template_id="4",
        personalisation={"data_set_name": dataset.live_revision.name},
    )


@pytest.mark.skip
def test_data_endpoint_unreachable_expiring(mocker, datasets):
    # Set up
    client = setup_mocking(mocker)
    dataset, org_user = datasets

    # Test
    client.send_data_endpoint_unreachable_expiring_notification(dataset)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=org_user.email,
        template_id="3",
        personalisation={
            "data_set_name": dataset.live_revision.name,
            "data_set_url": dataset.live_revision.url_link,
        },
    )


@pytest.mark.skip
def test_data_endpoint_deleted_notifying_deleting_user(mocker, user_factory):
    # Set up
    client = setup_mocking(mocker)

    # create Feed with operator and FeedSubscriber
    org_user = user_factory(account_type=AccountType.org_admin.value)
    deleting_user = user_factory(account_type=AccountType.org_admin.value)
    revision = DatasetRevisionFactory(
        last_modified_user=org_user, published_by=org_user
    )

    # Test
    client.send_data_endpoint_deleted_deleter_notification(revision, deleting_user)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=deleting_user.email,
        template_id="2",
        personalisation={"data_set_name": revision.name},
    )


@pytest.mark.skip
def test_data_endpoint_deleted_notifying_last_updated_user(mocker, user_factory):
    # Set up
    client = setup_mocking(mocker)

    # create Feed with operator and FeedSubscriber
    org_user = user_factory(account_type=AccountType.org_admin.value)
    revision = DatasetRevisionFactory(
        dataset__contact=org_user, last_modified_user=org_user, published_by=org_user
    )
    last_update_date = localize_datetime_and_convert_to_string(revision.modified)

    # Test
    client.send_data_endpoint_deleted_updater_notification(revision)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=org_user.email,
        template_id="1",
        personalisation={
            "data_set_name": revision.name,
            "last_update_date": last_update_date,
        },
    )


@pytest.mark.skip
def test_data_endpoint_has_expired(mocker, datasets):
    # Set up
    client = setup_mocking(mocker)
    dataset, org_user = datasets
    # create Feed with operator and FeedSubscriber

    published = localize_datetime_and_convert_to_string(
        dataset.live_revision.published_at
    )
    expiry = localize_datetime_and_convert_to_string(
        dataset.live_revision.first_expiring_service
    )
    # Test
    client.send_data_endpoint_deactivated_notification(dataset)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=org_user.email,
        template_id="11",
        personalisation={
            "feed_name": dataset.live_revision.name,
            "published_time": published,
            "expiry_time": expiry,
        },
    )


@pytest.mark.skip
def test_data_endpoint_expired_developer(mocker, user_factory):
    # Set up
    client = setup_mocking(mocker)

    # create Feed with operator and FeedSubscriber
    org_user = user_factory(account_type=AccountType.org_admin.value)
    bob = user_factory(name="bob", account_type=AccountType.developer.value)
    charlie = user_factory(name="charlie", account_type=AccountType.developer.value)
    dataset = DatasetFactory(
        subscribers=[bob, charlie], live_revision__last_modified_user=org_user
    )
    published = localize_datetime_and_convert_to_string(
        dataset.live_revision.published_at
    )
    expiry = localize_datetime_and_convert_to_string(
        dataset.live_revision.first_expiring_service
    )

    # Test
    client.send_developer_data_endpoint_expired_notification(dataset)

    # Assert
    bob_call = call(
        email_address=bob.email,
        template_id="11",
        personalisation={
            "feed_name": dataset.live_revision.name,
            "published_time": published,
            "expiry_time": expiry,
        },
    )

    charlie_call = call(
        email_address=charlie.email,
        template_id="11",
        personalisation={
            "feed_name": dataset.live_revision.name,
            "published_time": published,
            "expiry_time": expiry,
        },
    )

    client._notification_client.send_email_notification.assert_has_calls(
        [bob_call, charlie_call]
    )


@pytest.mark.skip
def test_data_endpoint_error(mocker, user_factory):
    # Set up
    client = setup_mocking(mocker)

    # create Feed with operator and FeedSubscriber
    org_user = user_factory(account_type=AccountType.org_admin.value)
    revision = DatasetRevisionFactory(
        dataset__contact=org_user, last_modified_user=org_user, published_by=org_user
    )
    DatasetETLErrorFactory(revision=revision, description="An error")
    DatasetETLErrorFactory(revision=revision, description="Big error")

    client = GovUKNotifyEmail()
    published = localize_datetime_and_convert_to_string(revision.published_at)
    errors = "An error, Big error"
    # Test
    client.send_data_endpoint_error_notification(revision)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=org_user.email,
        template_id="9",
        personalisation={
            "feed_name": revision.name,
            "published_time": published,
            "comments": revision.comment,
            "errors": errors,
        },
    )


@pytest.mark.skip
def test_data_endpoint_live(mocker, datasets):
    # Set up
    client = setup_mocking(mocker)

    # create Feed with operator and FeedSubscriber
    dataset, org_user = datasets
    published = localize_datetime_and_convert_to_string(
        dataset.live_revision.published_at
    )
    # Test
    client.send_data_endpoint_publish_notification(dataset)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=org_user.email,
        template_id="8",
        personalisation={
            "feed_name": dataset.live_revision.name,
            "published_time": published,
            "comments": dataset.live_revision.comment,
        },
    )


@pytest.mark.skip
def test_leave_feedback(mocker, datasets, user_factory):
    # Set up
    client = setup_mocking(mocker)
    dataset, org_user = datasets
    # create Feed with operator and FeedSubscriber
    dev = user_factory(account_type=AccountType.developer.value)
    feedback = "that doesnt work at all"

    # Test
    client.send_feedback_notification(dataset, feedback, dev)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=org_user.email,
        template_id="16",
        personalisation={
            "dataset_name": dataset.live_revision.name,
            "user_email": dev.email,
            "feedback": feedback,
        },
    )


@pytest.mark.skip
def test_invite_accepted(mocker, user_factory):
    # setup
    client = setup_mocking(mocker)
    org = OrganisationFactory.create()
    admin = user_factory(account_type=AccountType.org_admin.value, organisation=org)
    user_email = "newuser@test.test"
    new_user = user_factory(
        email=user_email, account_type=AccountType.org_staff.value, organisation=org
    )
    admin.settings.notify_invitation_accepted = True
    admin.settings.save()
    InvitationFactory.create(email=user_email, inviter=admin)

    # test
    client.send_invite_accepted_notification(new_user)

    # assert
    client._notification_client.send_email_notification.assert_called_with(
        email_address=admin.email,
        template_id="15",
        personalisation={
            "name": new_user.email,
            "organisation": new_user.organisation.name,
        },
    )


@pytest.mark.skip
def test_password_reset(mocker, user_factory):
    # Set up
    client = setup_mocking(mocker)

    # create Feed with operator and FeedSubscriber
    user = user_factory(account_type=AccountType.org_staff)
    token = "password_token"

    # Test
    client.send_password_reset_notification(token, user)

    # Assert
    client._notification_client.send_email_notification.assert_called_once_with(
        email_address=user.email,
        template_id="14",
        personalisation={"reset_link": token},
    )


@pytest.mark.skip
def test_invite_new_user(mocker, user_factory, request_factory):
    # setup
    client = setup_mocking(mocker)
    request = request_factory.get("/account/manage/invite/")
    admin = user_factory(account_type=AccountType.org_admin.value)
    invitation = InvitationFactory.create(email="newuser@test.test", inviter=admin)
    invitation.account_type = AccountType.org_staff.value
    invitation.organisation = admin.organisation
    invitation.save()

    # test
    client.send_invitation_notification(invitation, request)
    host = config.hosts.PUBLISH_HOST
    signup_link = reverse(
        "invitations:accept-invite", args=[invitation.key], host=host, scheme="http"
    )
    # assert
    client._notification_client.send_email_notification.assert_called_with(
        email_address="newuser@test.test",
        template_id="13",
        personalisation={
            "signup_link": signup_link,
            "organisation": admin.organisation.name,
        },
    )


@pytest.mark.skip
def test_verify_email_address(mocker, user_factory, request_factory):
    # setup
    client = setup_mocking(mocker)
    request = request_factory.get("/account/signup/")
    request.host = get_host(config.hosts.DATA_HOST)

    user = user_factory.create()
    email_address = EmailAddress(user=user, email="test@test.test")
    email_address.save()
    confirmation = EmailConfirmation.create(email_address)

    # test
    client.send_verify_email_address_notification(request, confirmation, signup=False)
    host = config.hosts.DATA_HOST
    signup_link = reverse(
        "account_confirm_email", args=[confirmation.key], host=host, scheme="http"
    )
    # assert
    client._notification_client.send_email_notification.assert_called_with(
        email_address="test@test.test",
        template_id="12",
        personalisation={"verify_link": signup_link},
    )
