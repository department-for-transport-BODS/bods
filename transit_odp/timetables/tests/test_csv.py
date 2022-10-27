import pytest
from factory import Sequence

from transit_odp.data_quality.factories import (
    DataQualityReportFactory,
    PTIValidationResultFactory,
)
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    LicenceFactory,
    ServiceCodeExemptionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models import Dataset
from transit_odp.otc.factories import ServiceModelFactory
from transit_odp.otc.models import Service
from transit_odp.timetables.csv import _get_timetable_catalogue_dataframe

pytestmark = pytest.mark.django_db


def test_service_in_bods_but_not_in_otc():
    for fa in TXCFileAttributesFactory.create_batch(
        5, service_code=Sequence(lambda n: f"PD00000{n}")
    ):
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)

    ServiceModelFactory.create_batch(5)

    df = _get_timetable_catalogue_dataframe()
    for index, row in df[:5].iterrows():
        dataset = Dataset.objects.get(id=row["Dataset ID"])
        txc_file_attributes = dataset.live_revision.txc_file_attributes.first()
        assert row["Service Statuses"] == "Unassigned licence"
        assert row["DQ Score"] == "33%"
        assert row["BODS Compliant"] == "NO"
        assert row["XML Filename"] == txc_file_attributes.filename
        assert row["Last Updated Date"] == dataset.live_revision.published_at
        assert (
            row["National Operator Code"] == txc_file_attributes.national_operator_code
        )
        assert row["Licence Number"] == txc_file_attributes.licence_number
        assert row["Service Code"] == txc_file_attributes.service_code
        assert row["Line Name"] == "line1 line2"
        assert row["Origin"] == txc_file_attributes.origin
        assert row["Destination"] == txc_file_attributes.destination


def test_service_in_bods_and_otc():
    for service in ServiceModelFactory.create_batch(5):
        fa = TXCFileAttributesFactory(
            licence_number=service.licence.number,
            service_code=service.registration_number.replace("/", ":"),
        )
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)

    df = _get_timetable_catalogue_dataframe()
    for index, row in df.iterrows():
        dataset = Dataset.objects.get(id=row["Dataset ID"])
        service = Service.objects.get(registration_number=row["Registration Number"])
        operator = service.operator
        licence = service.licence
        txc_file_attributes = dataset.live_revision.txc_file_attributes.first()
        assert row["Service Statuses"] == "Published (Registered)"
        assert row["DQ Score"] == "33%"
        assert row["BODS Compliant"] == "NO"
        assert row["XML Filename"] == txc_file_attributes.filename
        assert row["Last Updated Date"] == dataset.live_revision.published_at
        assert (
            row["National Operator Code"] == txc_file_attributes.national_operator_code
        )
        assert row["Licence Number"] == txc_file_attributes.licence_number
        assert row["Service Code"] == txc_file_attributes.service_code
        assert row["Line Name"] == "line1 line2"
        assert row["Origin"] == txc_file_attributes.origin
        assert row["Destination"] == txc_file_attributes.destination

        assert row["Operator ID"] == operator.operator_id
        assert row["Operator Name"] == operator.operator_name
        assert row["Address"] == operator.address
        assert row["OTC Licence Number"] == licence.number
        assert row["Registration Number"] == service.registration_number
        assert row["Service Number"] == service.service_number
        assert row["Start Point"] == service.start_point
        assert row["Finish Point"] == service.finish_point
        assert row["Via"] == service.via
        assert row["Granted Date"] == licence.granted_date
        assert row["Expiry Date"] == licence.expiry_date
        assert row["Effective Date"] == service.effective_date
        assert row["Received Date"] == service.received_date
        assert row["Service Type Other Details"] == service.service_type_other_details


def test_service_in_otc_and_not_in_bods():
    ServiceModelFactory.create_batch(5)
    TXCFileAttributesFactory.create_batch(5)

    df = _get_timetable_catalogue_dataframe()
    for index, row in df[5:].iterrows():
        service = Service.objects.get(registration_number=row["Registration Number"])
        operator = service.operator
        licence = service.licence

        assert row["Service Statuses"] == "Missing data"
        assert row["Operator ID"] == operator.operator_id
        assert row["Operator Name"] == operator.operator_name
        assert row["Address"] == operator.address
        assert row["OTC Licence Number"] == licence.number
        assert row["Registration Number"] == service.registration_number
        assert row["Service Number"] == service.service_number
        assert row["Start Point"] == service.start_point
        assert row["Finish Point"] == service.finish_point
        assert row["Via"] == service.via
        assert row["Granted Date"] == licence.granted_date
        assert row["Expiry Date"] == licence.expiry_date
        assert row["Effective Date"] == service.effective_date
        assert row["Received Date"] == service.received_date
        assert row["Service Type Other Details"] == service.service_type_other_details


def test_unregistered_services_in_bods():
    for fa in TXCFileAttributesFactory.create_batch(
        5, service_code=Sequence(lambda n: f"UZ00000{n}")
    ):
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)

    ServiceModelFactory.create_batch(5)

    df = _get_timetable_catalogue_dataframe()
    for index, row in df[:5].iterrows():
        dataset = Dataset.objects.get(id=row["Dataset ID"])
        txc_file_attributes = dataset.live_revision.txc_file_attributes.first()
        assert row["Service Statuses"] == "Published (Unregistered)"
        assert row["DQ Score"] == "33%"
        assert row["BODS Compliant"] == "NO"
        assert row["XML Filename"] == txc_file_attributes.filename
        assert row["Last Updated Date"] == dataset.live_revision.published_at
        assert (
            row["National Operator Code"] == txc_file_attributes.national_operator_code
        )
        assert row["Licence Number"] == txc_file_attributes.licence_number
        assert row["Service Code"] == txc_file_attributes.service_code
        assert row["Line Name"] == "line1 line2"
        assert row["Origin"] == txc_file_attributes.origin
        assert row["Destination"] == txc_file_attributes.destination


def test_exempted_services_in_bods() -> None:
    """
    In exported data when Registration Number is included in ExemptedServiceCodes
    the Service Status should be "Published (Out of scope)".
    In this test all existing entries's reg. numbers are exempted.
    """

    for service in ServiceModelFactory.create_batch(5):
        fa = TXCFileAttributesFactory(
            licence_number=service.licence.number,
            service_code=service.registration_number.replace("/", ":"),
        )
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)
        bods_lic = LicenceFactory(number=service.licence.number)
        ServiceCodeExemptionFactory(
            licence=bods_lic, registration_code=service.registration_code
        )

    df = _get_timetable_catalogue_dataframe()
    for _, row in df.iterrows():
        assert row["Service Statuses"] == "Published (Out of scope)"


def test_empty_otc_services():
    for fa in TXCFileAttributesFactory.create_batch(
        5, service_code=Sequence(lambda n: f"UZ00000{n}")
    ):
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)

    with pytest.raises(EmptyDataFrame):
        _get_timetable_catalogue_dataframe()


def test_empty_txc_services():
    ServiceModelFactory.create_batch(5)

    with pytest.raises(EmptyDataFrame):
        _get_timetable_catalogue_dataframe()


def test_duplicated_txc_services():
    for service in ServiceModelFactory.create_batch(5):
        fa = TXCFileAttributesFactory.create_batch(
            2,
            licence_number=service.licence.number,
            service_code=service.registration_number.replace("/", ":"),
        )[0]
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)

    df = _get_timetable_catalogue_dataframe()
    assert len(df) == 5


def test_all_txc_file_attributes_belong_to_live_revisions():
    """
    Protects BODP-4792: All TxC file attributes must belong to the datasets current
    live revision otherwise the csv will show old data from previous revisions
    """
    for i in range(5):
        dataset = DatasetFactory(live_revision=None)
        for _ in range(3):
            r = DatasetRevisionFactory(dataset=dataset)
            TXCFileAttributesFactory(
                revision=r, service_code=f"PD00000{i}", origin="old"
            )
            DataQualityReportFactory(revision=r)
            PTIValidationResultFactory(revision=r)

        latest_revision = DatasetRevisionFactory(dataset=dataset)
        TXCFileAttributesFactory(
            revision=latest_revision, service_code=f"PD00000{i}", origin="latest"
        )
        DataQualityReportFactory(revision=latest_revision, score=0.98)
        PTIValidationResultFactory(revision=latest_revision)

    ServiceModelFactory()

    df = _get_timetable_catalogue_dataframe()
    for index, row in df[:5].iterrows():
        assert row["Origin"] == "latest"
        assert row["DQ Score"] == "98%"
