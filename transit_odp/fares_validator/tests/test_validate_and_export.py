from pathlib import Path

import pytest
from django.core.files import File
from django.test import RequestFactory

from tests.integration.factories import OrganisationFactory, RevisionFactory
from transit_odp.fares_validator.views.export_excel import FaresXmlExporter
from transit_odp.fares_validator.views.validate import FaresXmlValidator
from transit_odp.organisation import models
from transit_odp.organisation.factories import OrganisationFactory

DATA_DIR = Path(__file__).parent / "data"

pytestmark = pytest.mark.django_db


def create_organisation(**kwargs):
    return OrganisationFactory(**kwargs)


def create_revision(**kwargs):
    return RevisionFactory(**kwargs)


def test_get_errors():
    organisation: models.Organisation = create_organisation()
    revision: models.DatasetRevision = create_revision()
    filepath = DATA_DIR / "fares_test_xml_pass.xml"
    with open(filepath, "rb") as zout:
        fares_xml_validator = FaresXmlValidator(
            File(zout, name="fares_test_xml.xml"), organisation.id, revision.id
        )
        result = fares_xml_validator.get_errors()
        if result:
            assert result.status_code == 200


def test_set_errors():
    test_values = [True, False]
    organisation: models.Organisation = create_organisation()
    revision: models.DatasetRevision = create_revision()

    for test in test_values:
        if test:
            expected = 200
            filepath = DATA_DIR / "fares_test_xml_pass.xml"
        else:
            expected = 201
            filepath = DATA_DIR / "fares_test_xml_fail.xml"
        with open(filepath, "rb") as zout:
            fares_xml_validator = FaresXmlValidator(
                File(zout, name="fares_test_xml.xml"), organisation.id, revision.id
            )
            result = fares_xml_validator.set_errors()
            if result:
                assert result.status_code == expected


def test_fares_validation_zip():
    test_values = [True, False]
    organisation: models.Organisation = create_organisation()
    revision: models.DatasetRevision = create_revision()
    for test in test_values:
        if test:
            expected = 200
            filepath = DATA_DIR / "fares_test_zip_pass.zip"
        else:
            expected = 201
            filepath = DATA_DIR / "fares_test_zip_fail.zip"
        with open(filepath, "rb") as zout:
            fares_xml_validator = FaresXmlValidator(
                File(zout, name="fares_test_xml.xml"), organisation.id, revision.id
            )
            result = fares_xml_validator.set_errors()
            if result:
                assert result.status_code == expected


def test_export_excel():
    obj_exporter = FaresXmlExporter()
    test_report = obj_exporter.get(RequestFactory, 1, 1)
    assert test_report.status_code == 200
