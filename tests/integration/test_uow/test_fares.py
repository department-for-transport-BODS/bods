from datetime import timedelta

import pytest
from django.utils.timezone import now
from freezegun import freeze_time
from tests.integration.factories import (
    FaresDatasetFactory,
    FaresPublicationFactory,
    OrganisationFactory,
    PublisherUserFactory,
)

from transit_odp.bods.domain.entities import Revision
from transit_odp.bods.domain.entities.identity import OrganisationId, PublicationId
from transit_odp.bods.domain.entities.publication import FaresDataset, FaresPublication
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
    return FaresPublicationFactory(**kwargs)


def create_dataset(
    dataset: models.Dataset, published_at=None, **kwargs
) -> models.DatasetRevision:
    is_published = published_at is not None
    revision = FaresDatasetFactory(
        dataset=dataset, is_published=is_published, published_at=published_at, **kwargs
    )
    if is_published:
        dataset.live_revision = revision
        dataset.save()
    return revision


class TestFaresRepository:
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
        expected = FaresPublication(
            id=PublicationId(id=record.id),
            organisation_id=OrganisationId(id=record.organisation_id),
            contact_user_id=UserId(id=publisher.id),
            live=None,
            draft=Revision[FaresDataset](
                created_at=NOW,
                published_at=None,
                published_by=None,
                has_error=False,
                dataset=FaresDataset(
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
        expected = FaresPublication(
            id=PublicationId(id=record.id),
            organisation_id=OrganisationId(id=record.organisation_id),
            contact_user_id=UserId(id=publisher.id),
            live=Revision[FaresDataset](
                created_at=NOW,
                published_at=NOW,
                published_by=UserId(id=publisher.id),
                has_error=False,
                dataset=FaresDataset(
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
