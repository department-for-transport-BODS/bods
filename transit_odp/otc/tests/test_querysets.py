import pytest

from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    DraftDatasetFactory,
)
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.organisation.factories import (
    OrganisationFactory,
    ServiceCodeExemptionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models.data import ServiceCodeExemption
from transit_odp.otc.constants import (
    FLEXIBLE_REG,
    SCHOOL_OR_WORKS,
    SubsidiesDescription,
)
from transit_odp.otc.factories import LicenceModelFactory, ServiceModelFactory
from transit_odp.otc.models import Licence
from transit_odp.otc.models import Service as OTCService

pytestmark = pytest.mark.django_db


def test_add_school_or_work_count():
    licence = LicenceModelFactory()
    expected = 4
    ServiceModelFactory.create_batch(
        expected, licence=licence, service_type_description=SCHOOL_OR_WORKS
    )
    ServiceModelFactory.create_batch(
        10, licence=licence, service_type_description=FLEXIBLE_REG
    )
    licences = Licence.objects.add_school_or_work_count()
    licence = licences.first()
    assert licence
    assert licence.school_or_work_count == expected


def test_add_flexible_registration_count():
    licence = LicenceModelFactory()
    expected = 9
    ServiceModelFactory.create_batch(
        4, licence=licence, service_type_description=SCHOOL_OR_WORKS
    )
    ServiceModelFactory.create_batch(
        expected, licence=licence, service_type_description=FLEXIBLE_REG
    )
    licences = Licence.objects.add_flexible_registration_count()
    licence = licences.first()
    assert licence
    assert licence.flexible_registration_count == expected


def test_add_school_or_work_and_subsidies_count():
    licence = LicenceModelFactory()
    expected = 8
    ServiceModelFactory.create_batch(
        expected,
        licence=licence,
        service_type_description=SCHOOL_OR_WORKS,
        subsidies_description=SubsidiesDescription.YES,
    )
    ServiceModelFactory.create_batch(
        5,
        licence=licence,
        service_type_description=SCHOOL_OR_WORKS,
        subsidies_description=SubsidiesDescription.IN_PART,
    )
    ServiceModelFactory.create_batch(
        5,
        licence=licence,
        service_type_description=FLEXIBLE_REG,
        subsidies_description=SubsidiesDescription.YES,
    )
    ServiceModelFactory.create_batch(
        10,
        licence=licence,
        service_type_description=FLEXIBLE_REG,
        subsidies_description=SubsidiesDescription.IN_PART,
    )
    licences = Licence.objects.add_school_or_work_and_subsidies_count()
    licence = licences.first()
    assert licence
    assert licence.school_or_work_and_subsidies_count == expected


def test_add_school_or_work_and_in_part_count():
    licence = LicenceModelFactory()
    expected = 7
    ServiceModelFactory.create_batch(
        5,
        licence=licence,
        service_type_description=SCHOOL_OR_WORKS,
        subsidies_description=SubsidiesDescription.YES,
    )
    ServiceModelFactory.create_batch(
        expected,
        licence=licence,
        service_type_description=SCHOOL_OR_WORKS,
        subsidies_description=SubsidiesDescription.IN_PART,
    )
    ServiceModelFactory.create_batch(
        5,
        licence=licence,
        service_type_description=FLEXIBLE_REG,
        subsidies_description=SubsidiesDescription.YES,
    )
    ServiceModelFactory.create_batch(
        10,
        licence=licence,
        service_type_description=FLEXIBLE_REG,
        subsidies_description=SubsidiesDescription.IN_PART,
    )
    licences = Licence.objects.add_school_or_work_and_in_part_count()
    licence = licences.first()
    assert licence
    assert licence.school_or_work_and_in_part_count == expected


def test_add_distinct_service_count():
    licence = LicenceModelFactory()
    ServiceModelFactory.create_batch(5, licence=licence, registration_number="12134")
    ServiceModelFactory.create_batch(5, licence=licence, registration_number="12135")
    licences = Licence.objects.add_distinct_service_count()
    licence = licences.first()
    assert licence
    assert licence.distinct_service_count == 2


def test_get_all_in_organisation():
    org1 = OrganisationFactory()
    org1_licence_number = "PD000001"
    BODSLicenceFactory(organisation=org1, number=org1_licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    dataset2 = DatasetFactory(organisation=org1)
    num_org1_services = 4
    org1_service_codes = [
        f"{org1_licence_number}:{n:03}" for n in range(num_org1_services)
    ]
    for code in org1_service_codes[:2]:
        TXCFileAttributesFactory(revision__dataset=dataset1, service_code=code)
    for code in org1_service_codes[2:]:
        TXCFileAttributesFactory(revision__dataset=dataset2, service_code=code)

    org2 = OrganisationFactory()
    org2_licence_number = "PD000002"
    BODSLicenceFactory(organisation=org2, number=org2_licence_number)
    dataset3 = DatasetFactory(organisation=org2)
    num_org2_services = 5
    org2_service_codes = [
        f"{org2_licence_number}:{n:03}" for n in range(num_org2_services)
    ]
    for code in org2_service_codes:
        TXCFileAttributesFactory(revision__dataset=dataset3, service_code=code)

    otc_lic1 = LicenceModelFactory(number=org1_licence_number)
    for code in org1_service_codes:
        ServiceModelFactory(licence=otc_lic1, registration_number=code)
    otc_lic2 = LicenceModelFactory(number=org2_licence_number)
    for code in org2_service_codes:
        ServiceModelFactory(licence=otc_lic2, registration_number=code)

    queryset = OTCService.objects.get_all_in_organisation(org1.id).add_service_code()
    assert queryset.count() == num_org1_services
    otc_service_codes = [s.service_code for s in queryset]
    assert sorted(otc_service_codes) == sorted(org1_service_codes)

    queryset = OTCService.objects.get_all_in_organisation(org2.id).add_service_code()
    assert queryset.count() == num_org2_services
    otc_service_codes = [s.service_code for s in queryset]
    assert sorted(otc_service_codes) == sorted(org2_service_codes)


def test_get_all_without_exempted_ones() -> None:
    org = OrganisationFactory()
    org_licence_number = "PD000001"
    num_org_services = 4
    org_service_codes = [f"{org_licence_number}:{n}" for n in range(num_org_services)]

    bods_lic = BODSLicenceFactory(organisation=org, number=org_licence_number)
    dataset1 = DatasetFactory(organisation=org)
    dataset2 = DatasetFactory(organisation=org)

    for code in org_service_codes[:2]:
        TXCFileAttributesFactory(revision__dataset=dataset1, service_code=code)
    for code in org_service_codes[2:]:
        TXCFileAttributesFactory(revision__dataset=dataset2, service_code=code)

    otc_lic = LicenceModelFactory(number=org_licence_number)
    for code in org_service_codes:
        ServiceModelFactory(licence=otc_lic, registration_number=code)

    ServiceCodeExemptionFactory(
        licence=bods_lic, registration_code=org_service_codes[0].split(":")[1]
    )

    queryset = OTCService.objects.get_all_without_exempted_ones(org.id)

    assert queryset.count() == num_org_services - 1

    otc_service_codes = [s.service_code for s in queryset]

    exempted_service_code = (
        ServiceCodeExemption.objects.add_service_code().first().service_code
    )
    org_service_codes.remove(exempted_service_code)

    assert sorted(otc_service_codes) == sorted(org_service_codes)


def test_get_missing_from_organisation():
    total_services = 7
    licence_number = "PD000001"
    all_service_codes = [f"{licence_number}:{n:03}" for n in range(total_services)]

    org1 = OrganisationFactory()
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset1.live_revision, service_code=all_service_codes[0]
    )
    TXCFileAttributesFactory(
        revision=dataset1.live_revision, service_code=all_service_codes[1]
    )
    dataset2 = DraftDatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(), service_code=all_service_codes[2]
    )
    live_revision = DatasetRevisionFactory(dataset=dataset2)
    TXCFileAttributesFactory(revision=live_revision, service_code=all_service_codes[3])

    otc_lic1 = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        ServiceModelFactory(licence=otc_lic1, registration_number=code)

    expected_missing_service_codes = all_service_codes[2:3] + all_service_codes[4:]
    queryset = OTCService.objects.get_missing_from_organisation(
        org1.id
    ).add_service_code()
    assert queryset.count() == len(expected_missing_service_codes)
    otc_service_codes = [s.service_code for s in queryset]
    assert sorted(otc_service_codes) == sorted(expected_missing_service_codes)
