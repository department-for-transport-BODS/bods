import pytest

from transit_odp.otc.constants import (
    FLEXIBLE_REG,
    SCHOOL_OR_WORKS,
    SubsidiesDescription,
)
from transit_odp.otc.factories import LicenceModelFactory, ServiceModelFactory
from transit_odp.otc.models import Licence

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
