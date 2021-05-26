from datetime import timedelta

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.timezone import now
from freezegun import freeze_time
from tests.integration.factories import (
    OrganisationFactory,
    PublisherUserFactory,
    TimetableDatasetFactory,
    TimetablePublicationFactory,
)

from transit_odp.bods.domain.entities import (
    AVLDataset,
    AVLPublication,
    Revision,
    TimetableDataset,
    TimetablePublication,
)
from transit_odp.bods.domain.entities.identity import OrganisationId, PublicationId
from transit_odp.bods.domain.entities.publication import FaresDataset, FaresPublication
from transit_odp.bods.domain.entities.user import UserId
from transit_odp.bods.service_layer.unit_of_work import UnitOfWork
from transit_odp.organisation import models
from transit_odp.organisation.constants import AVLFeedStatus, FeedStatus

pytestmark = pytest.mark.django_db(transaction=True)

NOW = now()
RECENT = NOW - timedelta(minutes=5)
DISTANT = NOW - timedelta(hours=1)


def create_organisation(**kwargs):
    return OrganisationFactory(**kwargs)


def create_publisher(organisation, **kwargs):
    user = PublisherUserFactory(organisations=(organisation,), **kwargs)
    organisation.key_contact = user
    organisation.save()
    return user


def create_publication(**kwargs):
    return TimetablePublicationFactory(**kwargs)


def create_dataset(
    dataset: models.Dataset, published_at=None, **kwargs
) -> models.DatasetRevision:
    is_published = published_at is not None
    revision = TimetableDatasetFactory(
        dataset=dataset, is_published=is_published, published_at=published_at, **kwargs
    )
    if is_published:
        dataset.live_revision = revision
        dataset.save()
    return revision


def create_file(name: str = "test.xml", content: bytes = b"new content") -> str:
    path = default_storage.save(name, ContentFile(content))
    return path


class TestPublication:
    # TODO - parameterise these tests to load Timetables and AVL publications

    def test_uow_can_retrieve_a_publication_with_draft(self):
        organisation: models.Organisation = create_organisation()
        publisher = create_publisher(organisation)

        with freeze_time(NOW):
            record = create_publication(organisation=organisation)
            create_dataset(dataset=record, published_at=None)
        draft_revision = record.revisions.get_draft().get()

        uow = UnitOfWork()
        with uow:
            [publication] = uow.publications.list()

        expected = TimetablePublication(
            id=PublicationId(id=record.id),
            organisation_id=OrganisationId(id=record.organisation_id),
            contact_user_id=UserId(id=publisher.id),
            live=None,
            draft=Revision[TimetableDataset](
                created_at=NOW,
                published_at=None,
                published_by=None,
                has_error=False,
                dataset=TimetableDataset(
                    name=draft_revision.name,
                    description=draft_revision.description,
                    short_description=draft_revision.short_description,
                    comment=draft_revision.comment,
                    url=draft_revision.url_link,
                    filename=draft_revision.upload_file.name,
                    has_expired=False,
                    report=None,
                ),
            ),
            events=[],
        )
        assert publication == expected  # Publication.__eq__ only compares identity
        assert publication.get_id() == record.id
        assert publication.organisation_id == expected.organisation_id
        assert publication.contact_user_id == expected.contact_user_id
        assert publication.live is None
        assert publication.draft == expected.draft

    def test_uow_can_retrieve_a_publication_with_live_revision(self):
        organisation: models.Organisation = create_organisation()
        publisher = create_publisher(organisation)

        with freeze_time(NOW):
            record = create_publication(organisation=organisation)
            create_dataset(dataset=record, published_at=NOW)

        uow = UnitOfWork()
        with uow:
            [publication] = uow.publications.list()

        live_revision = record.live_revision
        expected = TimetablePublication(
            id=PublicationId(id=record.id),
            organisation_id=OrganisationId(id=record.organisation_id),
            contact_user_id=UserId(id=publisher.id),
            live=Revision[TimetableDataset](
                created_at=NOW,
                published_at=NOW,
                published_by=live_revision.published_by_id,
                has_error=False,
                dataset=TimetableDataset(
                    name=live_revision.name,
                    description=live_revision.description,
                    short_description=live_revision.short_description,
                    comment=live_revision.comment,
                    url=live_revision.url_link,
                    filename=live_revision.upload_file.name,
                    has_expired=False,
                    report=None,
                ),
            ),
            draft=None,
            events=[],
        )

        assert publication == expected  # Publication.__eq__ only compares identity
        assert publication.get_id() == record.id
        assert publication.organisation_id == expected.organisation_id
        assert publication.contact_user_id == expected.contact_user_id
        assert publication.live == expected.live
        assert publication.draft is None

    def test_uow_can_retrieve_an_avl_publication_by_id(self):
        organisation: models.Organisation = create_organisation()
        create_publisher(organisation)
        record = create_publication(organisation=organisation)

        uow = UnitOfWork()
        with uow:
            publication = uow.publications.find(
                publication_id=PublicationId(id=record.id)
            )

        assert isinstance(publication, TimetablePublication)
        assert publication.get_id() == record.id

    def test_uow_returns_none_if_publication_not_found(self):
        uow = UnitOfWork()
        with uow:
            publication = uow.publications.find(publication_id=PublicationId(id=1000))
        assert publication is None

    def test_uow_can_retrieve_a_publication_with_draft_with_error(self):
        organisation: models.Organisation = create_organisation()
        create_publisher(organisation)

        with freeze_time(NOW):
            record = create_publication(organisation=organisation)
            create_dataset(
                dataset=record, published_at=None, status=FeedStatus.error.value
            )

        uow = UnitOfWork()
        with uow:
            [publication] = uow.publications.list()

        assert isinstance(publication.draft, Revision)
        assert publication.draft.has_error is True

    def test_uow_can_load_revision_history(self):
        organisation: models.Organisation = create_organisation()
        create_publisher(organisation)

        with freeze_time(DISTANT):
            record = create_publication(organisation=organisation)
            create_dataset(dataset=record, published_at=DISTANT)
        with freeze_time(RECENT):
            create_dataset(dataset=record, published_at=RECENT)
        with freeze_time(NOW):
            create_dataset(dataset=record, published_at=None)

        uow = UnitOfWork()
        with uow:
            revisions = uow.publications.get_revision_history(
                publication_id=PublicationId(id=record.id)
            )

        assert len(revisions) == 2
        assert [revision.published_at for revision in revisions] == [RECENT, DISTANT]

    def test_uow_can_save_a_timetable_publication(self):
        organisation: models.Organisation = create_organisation()
        publisher = create_publisher(organisation)

        txc_filename = create_file(content=b"secret content")

        uow = UnitOfWork()
        with uow:
            identity = uow.publications.next_identity()
            publication = TimetablePublication(
                id=identity,
                organisation_id=OrganisationId(id=organisation.id),
                contact_user_id=UserId(id=publisher.id),
                live=None,
                draft=Revision[TimetableDataset](
                    created_at=RECENT,
                    published_at=None,
                    published_by=None,
                    has_error=False,
                    dataset=TimetableDataset(
                        name="Test Dataset",
                        description="A test description",
                        short_description="Short description",
                        comment="A comment by the publisher",
                        url="https://www.example.com",
                        filename=txc_filename,
                        has_expired=False,
                        report=None,
                    ),
                ),
                events=[],
            )
            uow.publications.add(publication)
            uow.commit()

        [record] = models.Dataset.objects.all()
        assert record.id == identity.id
        assert record.organisation == organisation
        assert record.live_revision is None

        draft_revision = record.revisions.get_draft().get()
        assert draft_revision.created == RECENT
        assert draft_revision.published_at is None
        assert draft_revision.published_by is None
        assert draft_revision.status == FeedStatus.pending.value
        assert draft_revision.name == "Test Dataset"
        assert draft_revision.description == "A test description"
        assert draft_revision.short_description == "Short description"
        assert draft_revision.comment == "A comment by the publisher"
        assert draft_revision.url_link == "https://www.example.com"
        assert draft_revision.upload_file.name == txc_filename
        with draft_revision.upload_file.open("rb") as f:
            assert f.read() == b"secret content"

    def test_uow_can_save_a_fares_publication(self):
        organisation: models.Organisation = create_organisation()
        publisher = create_publisher(organisation)

        txc_filename = create_file(content=b"secret content")

        uow = UnitOfWork()
        with uow:
            identity = uow.publications.next_identity()
            publication = FaresPublication(
                id=identity,
                organisation_id=OrganisationId(id=organisation.id),
                contact_user_id=UserId(id=publisher.id),
                live=None,
                draft=Revision[FaresDataset](
                    created_at=RECENT,
                    published_at=None,
                    published_by=None,
                    has_error=False,
                    dataset=FaresDataset(
                        name="Test Dataset",
                        description="A test description",
                        short_description="Short description",
                        comment="A comment by the publisher",
                        url="https://www.example.com",
                        filename=txc_filename,
                        has_expired=False,
                        report=None,
                    ),
                ),
                events=[],
            )
            uow.publications.add(publication)
            uow.commit()

        [record] = models.Dataset.objects.all()
        assert record.id == identity.id
        assert record.organisation == organisation
        assert record.live_revision is None

        draft_revision = record.revisions.get_draft().get()
        assert draft_revision.created == RECENT
        assert draft_revision.published_at is None
        assert draft_revision.published_by is None
        assert draft_revision.status == FeedStatus.pending.value
        assert draft_revision.name == "Test Dataset"
        assert draft_revision.description == "A test description"
        assert draft_revision.short_description == "Short description"
        assert draft_revision.comment == "A comment by the publisher"
        assert draft_revision.url_link == "https://www.example.com"
        assert draft_revision.upload_file.name == txc_filename
        with draft_revision.upload_file.open("rb") as f:
            assert f.read() == b"secret content"

    def test_uow_can_save_an_avl_publication(self):
        """Tests that an AVLPublication is persisted to the DB"""
        organisation: models.Organisation = create_organisation()
        publisher = create_publisher(organisation)

        uow = UnitOfWork()
        with uow:
            identity = uow.publications.next_identity()
            publication = AVLPublication(
                id=identity,
                organisation_id=OrganisationId(id=organisation.id),
                contact_user_id=UserId(id=publisher.id),
                feed_status=AVLFeedStatus.FEED_UP,
                feed_last_checked=RECENT,
                live=None,
                draft=Revision[AVLDataset](
                    created_at=RECENT,
                    published_at=None,
                    published_by=None,
                    has_error=False,
                    dataset=AVLDataset(
                        name="Test Dataset",
                        description="A test description",
                        short_description="Short description",
                        comment="A comment by the publisher",
                        url="https://www.example.com",
                        username="user123",
                        password="password123",
                        requestor_ref="TestAccount",
                    ),
                ),
                events=[],
            )
            uow.publications.add(publication)
            uow.commit()

        [record] = models.Dataset.objects.all()
        assert record.id == identity.id
        assert record.organisation == organisation
        assert record.avl_feed_status == AVLFeedStatus.FEED_UP.value
        assert record.avl_feed_last_checked == RECENT
        assert record.live_revision is None

        draft_revision = record.revisions.get_draft().get()
        assert draft_revision.created == RECENT
        assert draft_revision.published_at is None
        assert draft_revision.published_by is None
        assert draft_revision.status == FeedStatus.pending.value
        assert draft_revision.name == "Test Dataset"
        assert draft_revision.description == "A test description"
        assert draft_revision.short_description == "Short description"
        assert draft_revision.comment == "A comment by the publisher"
        assert draft_revision.url_link == "https://www.example.com"
        assert draft_revision.username == "user123"
        assert draft_revision.password == "password123"
        assert draft_revision.requestor_ref == "TestAccount"

    def test_rolls_back_uncommitted_work_by_default(self):
        organisation: models.Organisation = create_organisation()
        publisher = create_publisher(organisation)
        txc_filename = create_file(content=b"secret content")

        uow = UnitOfWork()
        with uow:
            identity = uow.publications.next_identity()
            publication = TimetablePublication(
                id=identity,
                organisation_id=OrganisationId(id=organisation.id),
                contact_user_id=UserId(id=publisher.id),
                live=None,
                draft=Revision[TimetableDataset](
                    created_at=RECENT,
                    published_at=None,
                    published_by=None,
                    has_error=False,
                    dataset=TimetableDataset(
                        name="Test Dataset",
                        description="A test description",
                        short_description="Short description",
                        comment="A comment by the publisher",
                        url="https://www.example.com",
                        filename=txc_filename,
                        has_expired=False,
                        report=None,
                    ),
                ),
                events=[],
            )
            uow.publications.add(publication)

        assert not models.Dataset.objects.all().exists()

    def test_rolls_back_on_error(self):
        organisation: models.Organisation = create_organisation()
        publisher = create_publisher(organisation)
        txc_filename = create_file(content=b"secret content")

        class MyException(Exception):
            pass

        uow = UnitOfWork()
        with pytest.raises(MyException):
            with uow:
                identity = uow.publications.next_identity()
                publication = TimetablePublication(
                    id=identity,
                    organisation_id=OrganisationId(id=organisation.id),
                    contact_user_id=UserId(id=publisher.id),
                    live=None,
                    draft=Revision[TimetableDataset](
                        created_at=RECENT,
                        published_at=None,
                        published_by=None,
                        has_error=False,
                        dataset=TimetableDataset(
                            name="Test Dataset",
                            description="A test description",
                            short_description="Short description",
                            comment="A comment by the publisher",
                            url="https://www.example.com",
                            filename=txc_filename,
                            has_expired=False,
                            report=None,
                        ),
                    ),
                    events=[],
                )
                uow.publications.add(publication)
                raise MyException()

        assert not models.Dataset.objects.all().exists()
