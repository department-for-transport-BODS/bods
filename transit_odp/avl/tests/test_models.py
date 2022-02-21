import pytest

from transit_odp.avl.csv.validation import (
    SchemaValidationResponseExporter,
    ValidationReportExporter,
)
from transit_odp.avl.models import AVLSchemaValidationReport, AVLValidationReport
from transit_odp.avl.validation.factories import (
    ErrorFactory,
    IdentifierFactory,
    ResultFactory,
    SchemaErrorFactory,
    SchemaValidationResponseFactory,
    ValidationResponseFactory,
)
from transit_odp.avl.validation.models import ValidationSummary
from transit_odp.organisation.factories import AVLDatasetRevisionFactory

pytestmark = pytest.mark.django_db


def test_from_validation_response():
    """
    GIVEN a ValidationResponse object with 1 result, with 1 error
    WHEN I create a ValidationReportExporter and call to_csv_string
    THEN I am returned a valid csv formatted string with 1 header and 1 error row
    """

    summary = ValidationSummary(
        total_error_count=10,
        critical_error_count=1,
        non_critical_error_count=9,
        vehicle_activity_count=50,
        critical_score=0.9,
        non_critical_score=0.5,
    )

    identifier = IdentifierFactory(
        item_identifier="itemid1",
        line_ref="line13",
        name="OrginName",
        operator_ref="operator2",
        vehicle_journey_ref="vehicle_j_ref2",
        vehicle_ref="ref32",
    )
    error = ErrorFactory(
        level="Non-critical", details="Fake details", identifier=identifier
    )
    result = ResultFactory(errors=[error])
    response = ValidationResponseFactory(
        validation_summary=summary,
        results=[result],
    )
    revision = AVLDatasetRevisionFactory()
    AVLValidationReport.from_validation_response(
        revision_id=revision.id, response=response
    ).save()

    exporter = ValidationReportExporter(response=response)
    report = AVLValidationReport.objects.first()
    assert report.revision_id == revision.id
    assert report.critical_count == summary.critical_error_count
    assert report.non_critical_count == summary.non_critical_error_count
    assert report.critical_score == summary.critical_score
    assert report.non_critical_score == summary.non_critical_score
    assert report.vehicle_activity_count == summary.vehicle_activity_count
    assert report.file.name == exporter.get_filename()


def test_from_schema_validation_response():
    """
    GIVEN a SchemaValidationResponse object with 1 error
    WHEN I create a SchemaValidationReportExporter and call to_csv_string
    THEN I am returned a valid csv formatted string with 1 header and 1 error row
    """

    feed_id = 14
    errors = [SchemaErrorFactory()]
    response = SchemaValidationResponseFactory(feed_id=feed_id, errors=errors)
    revision = AVLDatasetRevisionFactory(id=feed_id)
    AVLSchemaValidationReport.from_schema_validation_response(
        revision_id=revision.id, response=response
    ).save()

    exporter = SchemaValidationResponseExporter(response=response)
    report = AVLSchemaValidationReport.objects.first()

    assert report.error_count == len(errors)
    assert report.file.name == exporter.get_filename()
