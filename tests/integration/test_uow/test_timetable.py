from datetime import timedelta
from typing import List

import pytest
from django.utils.timezone import now
from freezegun import freeze_time
from tests.integration.factories import (
    AdminAreaFactory,
    LocalityFactory,
    OrganisationFactory,
    PublisherUserFactory,
    TimetableDatasetFactory,
    TimetablePublicationFactory,
)

from transit_odp.bods.adapters.repositories import TimetableRepository
from transit_odp.bods.domain.entities import (
    Revision,
    TimetableDataset,
    TimetablePublication,
    TimetableReport,
)
from transit_odp.bods.domain.entities.identity import OrganisationId, PublicationId
from transit_odp.bods.domain.entities.user import UserId
from transit_odp.bods.service_layer.unit_of_work import UnitOfWork
from transit_odp.organisation import models
from transit_odp.organisation.constants import FeedStatus

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


def add_admin_areas(revision: models.DatasetRevision, names: List[str]):
    for name in names:
        revision.admin_areas.add(AdminAreaFactory(name=name))


def add_locality(revision: models.DatasetRevision, names: List[str]):
    for name in names:
        revision.localities.add(LocalityFactory(name=name))


class TestTimetableRepository:
    def test_uow_can_retrieve_a_publication_with_draft(self):
        organisation: models.Organisation = create_organisation()
        publisher = create_publisher(organisation)

        with freeze_time(NOW):
            record = create_publication(organisation=organisation)
            create_dataset(dataset=record, published_at=None)

        uow = UnitOfWork()
        with uow:
            [publication] = uow.publications.list()

        draft_revision = record.revisions.get_draft().get()
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
            create_dataset(dataset=record, published_at=NOW, published_by=publisher)

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
                published_by=UserId(id=publisher.id),
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

    def test_uow_can_retrieve_a_publication_with_expired_dataset(self):
        organisation: models.Organisation = create_organisation()
        publisher = create_publisher(organisation)

        with freeze_time(NOW):
            record = create_publication(organisation=organisation)
            create_dataset(
                dataset=record,
                published_at=NOW,
                published_by=publisher,
                status=FeedStatus.expired.value,
            )

        uow = UnitOfWork()
        with uow:
            [publication] = uow.publications.list()

        assert publication.live is not None
        assert publication.live.dataset.has_expired is True

    def test_uow_can_retrieve_a_publication_with_timetable_report(self):
        organisation: models.Organisation = create_organisation()
        publisher = create_publisher(organisation)

        with freeze_time(NOW):
            record = create_publication(organisation=organisation)
            revision = create_dataset(
                dataset=record,
                published_at=NOW,
                published_by=publisher,
                status=FeedStatus.expiring.value,
                transxchange_version="1.3",
                imported=RECENT,
                publisher_creation_datetime=DISTANT,
                publisher_modified_datetime=DISTANT,
                first_expiring_service=RECENT,
                last_expiring_service=RECENT,
                first_service_start=DISTANT,
                num_of_operators=1,
                num_of_lines=10,
                num_of_bus_stops=50,
            )
            add_admin_areas(revision, names=["Yorkshire", "Cambridgeshire"])
            add_locality(
                revision, names=["Valley Park", "South Widcombe", "Lyncombe Vale"]
            )

        repository = TimetableRepository()
        [publication] = repository.list()

        assert publication.live is not None
        assert publication.live.dataset.report == TimetableReport(
            transxchange_version="1.3",
            num_of_operators=1,
            num_of_lines=10,
            num_of_bus_stops=50,
            publisher_creation_datetime=DISTANT,
            publisher_modified_datetime=DISTANT,
            first_expiring_service=RECENT,
            last_expiring_service=RECENT,
            first_service_start=DISTANT,
            admin_areas=["Cambridgeshire", "Yorkshire"],
            localities=["Lyncombe Vale", "South Widcombe", "Valley Park"],
        )
