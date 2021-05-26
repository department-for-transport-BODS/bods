import pytest
from tests.integration.factories import OrganisationFactory

from transit_odp.bods.domain.entities import Organisation
from transit_odp.bods.domain.entities.identity import OrganisationId
from transit_odp.bods.service_layer.unit_of_work import UnitOfWork
from transit_odp.organisation import models as models

pytestmark = pytest.mark.django_db(transaction=True)


def create_organisation(**kwargs) -> models.Organisation:
    return OrganisationFactory(**kwargs)


class TestOrganisation:
    def test_uow_can_retrieve_an_organisation_by_id(self):
        record = create_organisation()

        uow = UnitOfWork()
        with uow:
            organisation = uow.organisations.find(
                organisation_id=OrganisationId(id=record.id)
            )

        assert isinstance(organisation, Organisation)
        assert organisation.id == OrganisationId(id=record.id)

    def test_uow_returns_none_if_organisation_not_found(self):
        uow = UnitOfWork()
        with uow:
            organisation = uow.organisations.find(
                organisation_id=OrganisationId(id=1000)
            )
        assert organisation is None

    def test_uow_can_retrieve_a_organisation(self):
        record = create_organisation()

        uow = UnitOfWork()
        with uow:
            [organisation] = uow.organisations.list()

        expected = Organisation(
            id=OrganisationId(id=record.id),
            name=record.name,
            short_name=record.short_name,
            is_active=True,
        )
        assert isinstance(organisation, Organisation)
        assert organisation == expected  # tests __eq__
        assert organisation.get_id() == record.id
        assert organisation.name == record.name
        assert organisation.short_name == record.short_name
        assert organisation.is_active

    def test_uow_can_save_a_organisation(self):
        organisation = Organisation(
            id=OrganisationId(id=1),
            name="East Yorkshire Motoring Service",
            short_name="EYMS",
            is_active=True,
        )

        uow = UnitOfWork()
        with uow:
            uow.organisations.add(organisation)
            uow.commit()

        [record] = models.Organisation.objects.all()
        assert record.id == organisation.get_id()
        assert record.name == organisation.name
        assert record.short_name == organisation.short_name
        assert record.is_active
