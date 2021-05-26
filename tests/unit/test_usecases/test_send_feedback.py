import pytest
from django.utils.timezone import now
from faker import Faker
from tests.stubs.cavl import FakeCAVLService
from tests.stubs.notifications import FakeNotifications
from tests.stubs.unit_of_work import FakeUnitOfWork

from transit_odp.bods.bootstrap import bootstrap
from transit_odp.bods.domain import commands
from transit_odp.bods.domain.entities import (
    Organisation,
    Publisher,
    Revision,
    TimetableDataset,
    TimetablePublication,
)
from transit_odp.bods.domain.entities.identity import (
    OrganisationId,
    PublicationId,
    UserId,
)
from transit_odp.bods.domain.entities.user import Email, User
from transit_odp.bods.interfaces.unit_of_work import IUnitOfWork

faker = Faker()


def create_organisation(uow: IUnitOfWork, is_active=True, **kwargs) -> Organisation:
    identity = uow.organisations.next_identity()
    return Organisation(
        id=identity,
        name=faker.company(),
        short_name=faker.company(),
        is_active=is_active,
        **kwargs
    )


def create_consumer(uow: IUnitOfWork, **kwargs) -> User:
    identity = uow.publications.next_identity()
    return User(
        id=identity,
        email=Email(faker.email()),
        mute_all_dataset_notifications=False,
        **kwargs
    )


def create_publisher(
    uow: IUnitOfWork,
    organisation: Organisation,
    is_admin=True,
    notify_avl_unavailable=False,
    mute_all_dataset_notifications=False,
    **kwargs
) -> Publisher:
    identity = uow.users.next_identity()
    return Publisher(
        id=identity,
        email=Email(faker.email()),
        organisation_id=organisation.id,
        is_admin=is_admin,
        notify_avl_unavailable=notify_avl_unavailable,
        mute_all_dataset_notifications=mute_all_dataset_notifications,
        **kwargs
    )


def create_publication(
    uow: IUnitOfWork, publisher: Publisher, **kwargs
) -> TimetablePublication:
    identity = uow.publications.next_identity()
    return TimetablePublication(
        id=identity,
        organisation_id=publisher.organisation_id,
        contact_user_id=publisher.id,
        live=Revision[TimetableDataset](
            created_at=now(),
            published_at=None,
            published_by=None,
            has_error=False,
            dataset=TimetableDataset(
                name=faker.name(),
                description=faker.sentence(),
                short_description=faker.sentence(),
                comment=faker.sentence(),
                url=faker.uri(),
                has_expired=False,
                **kwargs
            ),
        ),
        draft=None,
        events=[],
    )


class TestSendFeedback:
    @pytest.mark.parametrize(
        "anonymous, email",
        [(True, "OPERATOR_FEEDBACK-anonymous"), (False, "OPERATOR_FEEDBACK")],
        ids=["anonymous", "signed"],
    )
    def test_feedback_is_sent(self, anonymous, email):
        uow = FakeUnitOfWork()
        with uow:
            organisation = create_organisation(uow)
            publisher = create_publisher(uow, organisation=organisation)
            publication = create_publication(uow, publisher=publisher)
            consumer = create_consumer(uow)

            uow.publications.add(publication)
            uow.organisations.add(organisation)
            uow.users.add(publisher)
            uow.users.add(consumer)

        notifications = FakeNotifications()
        bus = bootstrap(
            uow=uow, notifications=notifications, cavl_service=FakeCAVLService()
        )

        bus.handle(
            commands.SendFeedback(
                sender_id=consumer.id,
                publication_id=publication.id,
                feedback="The TxC data is missing a number of schedules",
                anonymous=anonymous,
            )
        )

        assert notifications.sent[publisher.email] == [email]
        assert uow.committed

    def test_feedback_is_not_sent_to_archived_organisation(self):
        uow = FakeUnitOfWork()
        with uow:
            organisation = create_organisation(uow, is_active=False)
            publisher = create_publisher(uow, organisation=organisation)
            publication = create_publication(uow, publisher=publisher)
            consumer = create_consumer(uow)

            uow.publications.add(publication)
            uow.organisations.add(organisation)
            uow.users.add(publisher)
            uow.users.add(consumer)

        notifications = FakeNotifications()
        bus = bootstrap(
            uow=uow, notifications=notifications, cavl_service=FakeCAVLService()
        )

        bus.handle(
            commands.SendFeedback(
                sender_id=consumer.id,
                publication_id=publication.id,
                feedback="The TxC data is missing a number of schedules",
                anonymous=False,
            )
        )

        assert not notifications.sent[publisher.email]
        assert not uow.committed
