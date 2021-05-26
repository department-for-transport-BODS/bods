from typing import cast

import pytest
from django.utils.timezone import now

from tests.integration.factories import OrganisationFactory, PublisherUserFactory
from tests.stubs.cavl import FakeCAVLService
from tests.stubs.notifications import FakeNotifications
from tests.stubs.unit_of_work import FakeUnitOfWork
from transit_odp.bods.bootstrap import bootstrap
from transit_odp.bods.domain import commands
from transit_odp.bods.domain.entities import (
    AVLDataset,
    AVLPublication,
    Organisation,
    Revision,
)
from transit_odp.bods.domain.entities.identity import OrganisationId, PublicationId
from transit_odp.bods.domain.entities.user import Email, Publisher, User, UserId
from transit_odp.organisation.constants import AVLFeedStatus

NOW = now()


def create_organisation(**kwargs):
    return OrganisationFactory(**kwargs)


def create_publisher(organisation, **kwargs):
    user = PublisherUserFactory(organisation=organisation, **kwargs)
    organisation.key_contact = user
    organisation.save()
    return user


@pytest.fixture
def publication():
    return AVLPublication(
        id=PublicationId(id=1),
        organisation_id=OrganisationId(id=1),
        contact_user_id=UserId(id=1),
        live=Revision[AVLDataset](
            created_at=NOW,
            published_at=None,
            published_by=None,
            has_error=False,
            dataset=AVLDataset(
                name="Test Feed",
                description="Descriptive text",
                short_description="Short description",
                comment="Initial publication",
                url="http://www.test-feed.com",
                username="account123",
                password="password123",
                requestor_ref="",
            ),
        ),
        draft=None,
        events=[],
    )


def register_feed_with_status(
    cavl_service: FakeCAVLService, publication: AVLPublication, status: AVLFeedStatus
):
    feed_id = publication.get_id()
    assert publication.live
    cavl_service.register_feed(
        feed_id=feed_id,
        publisher_id=publication.organisation_id.id,
        url=publication.live.dataset.url,
        username=publication.live.dataset.username,
        password=publication.live.dataset.password,
    )
    cavl_service._set_feed_status(feed_id, status)


class TestMonitorAVLFeeds:
    def test_publication_feed_status_is_updated(self, publication):
        uow = FakeUnitOfWork()
        # TODO - add publication through command
        uow.publications.add(publication)

        cavl_service = FakeCAVLService()
        register_feed_with_status(cavl_service, publication, AVLFeedStatus.FEED_UP)

        notifications = FakeNotifications()
        bus = bootstrap(uow=uow, notifications=notifications, cavl_service=cavl_service)

        bus.handle(commands.MonitorAVLFeeds())

        actual = cast(
            AVLPublication, bus.uow.publications.find(publication_id=publication.id)
        )
        assert actual.feed_status == AVLFeedStatus.FEED_UP
        assert not notifications.sent
        assert uow.committed

    def test_sends_publisher_notification_on_avl_feed_down(self):
        organisation = Organisation(
            id=OrganisationId(id=1),
            name="Organisation name",
            short_name="org",
            is_active=True,
        )
        publisher = Publisher(
            id=UserId(id=1),
            email=Email("user@test.com"),
            organisation_id=organisation.id,
            is_admin=False,
            notify_avl_unavailable=True,  # user opted for avl down notifications
            mute_all_dataset_notifications=False,
        )

        publication = AVLPublication(
            id=PublicationId(id=1),
            organisation_id=organisation.id,
            contact_user_id=publisher.id,
            live=Revision[AVLDataset](
                created_at=NOW,
                published_at=None,
                published_by=None,
                has_error=False,
                dataset=AVLDataset(
                    name="Test Feed",
                    description="Descriptive text",
                    short_description="Short description",
                    comment="Initial publication",
                    url="http://www.test-feed.com",
                    username="account123",
                    password="password123",
                    requestor_ref="",
                    id=1,
                ),
            ),
            draft=None,
            events=[],
        )

        uow = FakeUnitOfWork()
        uow.organisations.add(organisation)
        uow.users.add(publisher)
        uow.publications.add(publication)

        cavl_service = FakeCAVLService()
        register_feed_with_status(cavl_service, publication, AVLFeedStatus.FEED_DOWN)

        notifications = FakeNotifications()

        # test should be idempotent (only 1 notification is sent)
        bus = bootstrap(uow=uow, notifications=notifications, cavl_service=cavl_service)
        bus.handle(commands.MonitorAVLFeeds())
        bus.handle(commands.MonitorAVLFeeds())
        bus.handle(commands.MonitorAVLFeeds())

        actual = cast(
            AVLPublication, bus.uow.publications.find(publication_id=publication.id)
        )
        assert actual.feed_status == AVLFeedStatus.FEED_DOWN
        assert notifications.sent[publisher.email] == [
            "OPERATOR_AVL_ENDPOINT_UNREACHABLE"
        ]
        assert uow.committed

    def test_does_not_send_publisher_notification_on_avl_feed_down(self):
        publisher = Publisher(
            id=UserId(id=1),
            email=Email("user@test.com"),
            organisation_id=OrganisationId(id=1),
            is_admin=False,
            notify_avl_unavailable=False,  # user not opted for avl down notifications
        )

        publication = AVLPublication(
            id=PublicationId(id=1),
            organisation_id=OrganisationId(id=1),
            contact_user_id=publisher.id,
            live=Revision[AVLDataset](
                created_at=NOW,
                published_at=None,
                published_by=None,
                has_error=False,
                dataset=AVLDataset(
                    name="Test Feed",
                    description="Descriptive text",
                    short_description="Short description",
                    comment="Initial publication",
                    url="http://www.test-feed.com",
                    username="account123",
                    password="password123",
                    requestor_ref="",
                ),
            ),
            draft=None,
            events=[],
        )

        uow = FakeUnitOfWork()
        uow.users.add(publisher)
        uow.publications.add(publication)

        cavl_service = FakeCAVLService()
        register_feed_with_status(cavl_service, publication, AVLFeedStatus.FEED_DOWN)

        notifications = FakeNotifications()

        # test should be idempotent (only 1 notification is sent)
        bus = bootstrap(uow=uow, notifications=notifications, cavl_service=cavl_service)
        bus.handle(commands.MonitorAVLFeeds())
        bus.handle(commands.MonitorAVLFeeds())
        bus.handle(commands.MonitorAVLFeeds())

        actual = cast(
            AVLPublication, bus.uow.publications.find(publication_id=publication.id)
        )
        assert actual.feed_status == AVLFeedStatus.FEED_DOWN
        assert len(notifications.sent) == 0
        assert uow.committed

    def test_sends_subscriber_notification_on_avl_feed_down(self):
        organisation = Organisation(
            id=OrganisationId(id=1),
            name="Organisation name",
            short_name="org",
            is_active=True,
        )
        publisher = Publisher(
            id=UserId(id=1),
            email=Email("user@test.com"),
            organisation_id=organisation.id,
            is_admin=False,
            notify_avl_unavailable=True,  # user opted for avl down notifications
        )

        developer = User(
            id=UserId(id=10),
            email=Email("developer@test.com"),
            mute_all_dataset_notifications=False,  # receive notification
        )

        publication = AVLPublication(
            id=PublicationId(id=1),
            organisation_id=organisation.id,
            contact_user_id=publisher.id,
            subscribers=[
                developer.id,
            ],
            live=Revision[AVLDataset](
                created_at=NOW,
                published_at=None,
                published_by=None,
                has_error=False,
                dataset=AVLDataset(
                    name="Test Feed",
                    description="Descriptive text",
                    short_description="Short description",
                    comment="Initial publication",
                    url="http://www.test-feed.com",
                    username="account123",
                    password="password123",
                    requestor_ref="",
                    id=1,
                ),
            ),
            draft=None,
            events=[],
        )

        uow = FakeUnitOfWork()
        uow.organisations.add(organisation)
        uow.users.add(publisher)
        uow.users.add(developer)
        uow.publications.add(publication)

        cavl_service = FakeCAVLService()
        register_feed_with_status(cavl_service, publication, AVLFeedStatus.FEED_DOWN)

        notifications = FakeNotifications()

        # test should be idempotent (only 1 notification is sent)
        bus = bootstrap(uow=uow, notifications=notifications, cavl_service=cavl_service)
        bus.handle(commands.MonitorAVLFeeds())
        bus.handle(commands.MonitorAVLFeeds())
        bus.handle(commands.MonitorAVLFeeds())

        actual = cast(
            AVLPublication, bus.uow.publications.find(publication_id=publication.id)
        )
        assert actual.feed_status == AVLFeedStatus.FEED_DOWN
        assert (
            len(notifications.sent) == 2
        )  # One for publisher and one for user who has subscribed for the feed
        assert notifications.sent[developer.email] == [
            "DEVELOPER_AVL_FEED_STATUS_NOTIFICATION"
        ]
        assert uow.committed

    def test_does_not_send_subscriber_notification_on_avl_feed_down(self):
        organisation = Organisation(
            id=OrganisationId(id=1),
            name="Organisation name",
            short_name="org",
            is_active=True,
        )
        publisher = Publisher(
            id=UserId(id=1),
            email=Email("user@test.com"),
            organisation_id=organisation.id,
            is_admin=False,
            notify_avl_unavailable=True,  # user opted for avl down notifications
        )

        developer = User(
            id=UserId(id=10),
            email=Email("developer@test.com"),
            mute_all_dataset_notifications=True,
        )

        publication = AVLPublication(
            id=PublicationId(id=1),
            organisation_id=organisation.id,
            contact_user_id=publisher.id,
            subscribers=[
                developer.id,
            ],
            live=Revision[AVLDataset](
                created_at=NOW,
                published_at=None,
                published_by=None,
                has_error=False,
                dataset=AVLDataset(
                    name="Test Feed",
                    description="Descriptive text",
                    short_description="Short description",
                    comment="Initial publication",
                    url="http://www.test-feed.com",
                    username="account123",
                    password="password123",
                    requestor_ref="",
                    id=1,
                ),
            ),
            draft=None,
            events=[],
        )

        uow = FakeUnitOfWork()
        uow.organisations.add(organisation)
        uow.users.add(publisher)
        uow.users.add(developer)
        uow.publications.add(publication)

        cavl_service = FakeCAVLService()
        register_feed_with_status(cavl_service, publication, AVLFeedStatus.FEED_DOWN)

        notifications = FakeNotifications()

        # test should be idempotent (only 1 notification is sent)
        bus = bootstrap(uow=uow, notifications=notifications, cavl_service=cavl_service)
        bus.handle(commands.MonitorAVLFeeds())
        bus.handle(commands.MonitorAVLFeeds())
        bus.handle(commands.MonitorAVLFeeds())

        actual = cast(
            AVLPublication, bus.uow.publications.find(publication_id=publication.id)
        )
        assert actual.feed_status == AVLFeedStatus.FEED_DOWN
        assert len(notifications.sent) == 1  # publisher notification
        assert notifications.sent[publisher.email] == [
            "OPERATOR_AVL_ENDPOINT_UNREACHABLE"
        ]
        assert developer.email not in notifications.sent.keys()
        assert uow.committed
