from datetime import date, datetime, timedelta

import pytest
from factory import Sequence
from freezegun import freeze_time

from transit_odp.data_quality.factories import (
    DataQualityReportFactory,
    PTIValidationResultFactory,
)
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    LicenceFactory,
    OrganisationFactory,
    SeasonalServiceFactory,
    ServiceCodeExemptionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models import Dataset
from transit_odp.otc.factories import LicenceModelFactory, ServiceModelFactory
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
        assert row["Published Status"] == "Published"
        assert row["OTC Status"] == "Unregistered"
        assert row["Scope Status"] == "In Scope"
        assert row["DQ Score"] == "33%"
        assert row["BODS Compliant"] == "NO"
        assert row["XML Filename"] == txc_file_attributes.filename
        assert row["Last Updated Date"] == dataset.live_revision.published_at
        assert (
            row["National Operator Code"] == txc_file_attributes.national_operator_code
        )
        assert row["Data set Licence Number"] == txc_file_attributes.licence_number
        assert row["Data set Service Code"] == txc_file_attributes.service_code
        assert row["Data set Line Name"] == "line1 line2"
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
        service = Service.objects.get(
            registration_number=row["OTC Registration Number"]
        )
        operator = service.operator
        licence = service.licence
        txc_file_attributes = dataset.live_revision.txc_file_attributes.first()
        assert row["Published Status"] == "Published"
        assert row["OTC Status"] == "Registered"
        assert row["Scope Status"] == "In Scope"
        assert row["DQ Score"] == "33%"
        assert row["BODS Compliant"] == "NO"
        assert row["XML Filename"] == txc_file_attributes.filename
        assert row["Last Updated Date"] == dataset.live_revision.published_at
        assert (
            row["National Operator Code"] == txc_file_attributes.national_operator_code
        )
        assert row["Data set Licence Number"] == txc_file_attributes.licence_number
        assert row["Data set Service Code"] == txc_file_attributes.service_code
        assert row["Data set Line Name"] == "line1 line2"
        assert row["Origin"] == txc_file_attributes.origin
        assert row["Destination"] == txc_file_attributes.destination

        assert row["Operator ID"] == operator.operator_id
        assert row["Operator Name"] == operator.operator_name
        assert row["Address"] == operator.address
        assert row["OTC Licence Number"] == licence.number
        assert row["OTC Registration Number"] == service.registration_number
        assert row["OTC Service Number"] == service.service_number
        assert row["Start Point"] == service.start_point
        assert row["Finish Point"] == service.finish_point
        assert row["Via"] == service.via
        assert row["Granted Date"] == licence.granted_date
        assert row["Expiry Date"] == licence.expiry_date
        assert row["Effective Date"] == service.effective_date
        assert row["Received Date"] == service.received_date
        assert row["Service Type Other Details"] == service.service_type_other_details


def test_service_in_otc_and_not_in_bods():
    licence_number = "PD0000099"
    org_name = "test_org_1"
    org1 = OrganisationFactory(name=org_name)
    LicenceFactory(organisation=org1, number=licence_number)
    otc_lic = LicenceModelFactory(id=10, number=licence_number)
    ServiceModelFactory(licence=otc_lic)
    TXCFileAttributesFactory()

    df = _get_timetable_catalogue_dataframe()

    for _, row in df[1:].iterrows():
        service = Service.objects.get(
            registration_number=row["OTC Registration Number"]
        )
        operator = service.operator
        licence = service.licence

        assert row["Published Status"] == "Unpublished"
        assert row["OTC Status"] == "Registered"
        assert row["Scope Status"] == "In Scope"
        assert row["Operator ID"] == operator.operator_id
        assert row["Operator Name"] == operator.operator_name
        assert row["Address"] == operator.address
        assert row["OTC Licence Number"] == licence.number
        assert row["OTC Registration Number"] == service.registration_number
        assert row["OTC Service Number"] == service.service_number
        assert row["Start Point"] == service.start_point
        assert row["Finish Point"] == service.finish_point
        assert row["Via"] == service.via
        assert row["Granted Date"] == licence.granted_date
        assert row["Expiry Date"] == licence.expiry_date
        assert row["Effective Date"] == service.effective_date
        assert row["Received Date"] == service.received_date
        assert row["Service Type Other Details"] == service.service_type_other_details
        assert row["Requires Attention"] == "Yes"
        # Test organisation name when status is unpublished:
        assert row["Organisation Name"] == org_name


def test_service_in_otc_and_not_in_bods_no_organisation_name_created():
    ServiceModelFactory.create_batch(5)
    TXCFileAttributesFactory.create_batch(5)

    df = _get_timetable_catalogue_dataframe()

    for _, row in df[5:].iterrows():
        assert row["Published Status"] == "Unpublished"
        assert row["Organisation Name"] == "Organisation not yet created"


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
        assert row["Published Status"] == "Published"
        assert row["OTC Status"] == "Unregistered"
        assert row["Scope Status"] == "In Scope"
        assert row["DQ Score"] == "33%"
        assert row["BODS Compliant"] == "NO"
        assert row["XML Filename"] == txc_file_attributes.filename
        assert row["Last Updated Date"] == dataset.live_revision.published_at
        assert (
            row["National Operator Code"] == txc_file_attributes.national_operator_code
        )
        assert row["Data set Licence Number"] == txc_file_attributes.licence_number
        assert row["Data set Service Code"] == txc_file_attributes.service_code
        assert row["Data set Line Name"] == "line1 line2"
        assert row["Origin"] == txc_file_attributes.origin
        assert row["Destination"] == txc_file_attributes.destination


def test_exempted_services_in_bods() -> None:
    """
    In exported data when Registration Number is included in ExemptedServiceCodes
    the Scope Status should be "Out of Scope".
    In this test all existing entries' reg. numbers are exempted.
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
        assert row["Published Status"] == "Published"
        assert row["OTC Status"] == "Registered"
        assert row["Scope Status"] == "Out of Scope"


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


@freeze_time("2023-02-14")
@pytest.mark.parametrize(
    "start, end, status",
    (
        ("2023-01-01", "2023-02-01", "Out of Season"),
        ("2023-02-01", "2023-03-01", "In Season"),
        ("2023-03-01", "2023-04-01", "Out of Season"),
        (None, None, "Not Seasonal"),
    ),
)
def test_seasonal_status(start, end, status):
    """
    Exported services have a Seasonal Status with one of the following values:
    In Season - the service is marked as seasonal with dates that encompass
                today's date
    Out of Season - the service is marked as seasonal with dates that do not
                encompass today's date
    Not Seasonal - the service is not marked as seasonal
    """
    otc_service = ServiceModelFactory()
    txc = TXCFileAttributesFactory(
        licence_number=otc_service.licence.number,
        service_code=otc_service.registration_number.replace("/", ":"),
    )
    DataQualityReportFactory(revision=txc.revision)
    PTIValidationResultFactory(revision=txc.revision)
    bods_licence = LicenceFactory(number=otc_service.licence.number)
    if start is not None:
        SeasonalServiceFactory(
            licence=bods_licence,
            registration_code=otc_service.registration_code,
            start=date.fromisoformat(start),
            end=date.fromisoformat(end),
        )

    df = _get_timetable_catalogue_dataframe()
    assert df["Seasonal Status"][0] == status


@freeze_time("2023-02-14")
@pytest.mark.parametrize(
    "effective, modified, period_end, is_stale",
    (
        # All conditions satisfied for staleness
        ("2022-01-01", "2022-06-01", "2023-03-01", True),
        # End date not present
        ("2022-01-01", "2022-06-01", None, False),
        # Operating end date is not less than 42 day
        # look ahead
        ("2021-01-01", "2021-06-01", "2023-05-01", False),
        # Staleness status is set to OTC Variation
        ("2023-03-01", "2022-11-01", "2023-03-01", False),
    ),
)
def test_stale_42_day_look_ahead(effective, modified, period_end, is_stale):
    """
    Staleness Status - Stale - 42 day look ahead
    If “Effective stale date due to end date” (if present)  is sooner than
    “Effective stale date due to effective last modified date”
    and today’s date from which the file is created equals or passes
    “Effective stale date due to end date”
    and Last modified date < OTC Effective start date - FALSE
    """
    otc_service = ServiceModelFactory(effective_date=date.fromisoformat(effective))
    txc = TXCFileAttributesFactory(
        licence_number=otc_service.licence.number,
        service_code=otc_service.registration_number.replace("/", ":"),
        modification_datetime=datetime.fromisoformat(modified + "T00:00:00+00:00"),
        operating_period_start_date=None
        if period_end is None
        else date.fromisoformat(period_end) - timedelta(days=100),
        operating_period_end_date=None
        if period_end is None
        else date.fromisoformat(period_end),
    )
    DataQualityReportFactory(revision=txc.revision)
    PTIValidationResultFactory(revision=txc.revision)
    LicenceFactory(number=otc_service.licence.number)

    df = _get_timetable_catalogue_dataframe()
    assert (df["Staleness Status"][0] == "Stale - 42 day look ahead") == is_stale
    assert df["Requires Attention"][0] == "Yes" if is_stale else "No"


@freeze_time("2023-02-14")
@pytest.mark.parametrize(
    "effective, modified, period_end, is_stale",
    (
        # All conditions satisfied for staleness
        ("2021-12-01", "2022-01-01", "2023-06-01", True),
        # End date not present
        ("2021-12-01", "2022-01-01", None, True),
        # First condition not satisfied
        ("2021-01-01", "2021-06-01", "2022-05-01", False),
        # Second condition not satisfied
        ("2022-05-01", "2022-06-01", "2023-12-01", False),
        # Third condition not satisfied
        ("2022-02-01", "2022-01-01", "2023-03-01", False),
    ),
)
def test_stale_12_months_old(effective, modified, period_end, is_stale):
    """
    Staleness Status - Stale - 12 months old
    If “Effective stale date due to effective last modified” date is sooner
    than “Effective stale date due to end date” (if present)
    and today’s date from which the file is created equals or passes
    “Effective stale date due to effective last modified date”
    and Last modified date < OTC Effective start date - FALSE
    """
    otc_service = ServiceModelFactory(effective_date=date.fromisoformat(effective))
    txc = TXCFileAttributesFactory(
        licence_number=otc_service.licence.number,
        service_code=otc_service.registration_number.replace("/", ":"),
        modification_datetime=datetime.fromisoformat(modified + "T00:00:00+00:00"),
        operating_period_start_date=None
        if period_end is None
        else date.fromisoformat(period_end) - timedelta(days=100),
        operating_period_end_date=None
        if period_end is None
        else date.fromisoformat(period_end),
    )
    DataQualityReportFactory(revision=txc.revision)
    PTIValidationResultFactory(revision=txc.revision)
    LicenceFactory(number=otc_service.licence.number)

    df = _get_timetable_catalogue_dataframe()
    assert (df["Staleness Status"][0] == "Stale - 12 months old") == is_stale
    assert df["Requires Attention"][0] == "Yes" if is_stale else "No"


@freeze_time("2023-02-14")
@pytest.mark.parametrize(
    "effective, modified, period_end, period_start, is_stale",
    (
        # associated data No and today < effective stale date
        ("2023-04-01", "2023-01-01", "2025-01-01", "2022-01-01", False),
        # operating period start = effective date, so association data Yes
        # and today < effective stale date
        ("2023-04-01", "2023-01-01", "2025-01-01", "2023-04-01", False),
        # last modified date > associatoin date , so association data Yes
        # and today > effective stale date
        ("2023-03-01", "2023-02-01", "2025-01-01", "2023-01-01", False),
        # associated data No and today > effective stale date
        ("2023-03-01", "2022-12-01", "2025-01-01", "2023-01-01", True),
    ),
)
def test_stale_otc_variation(effective, modified, period_end, period_start, is_stale):
    """
    Staleness Status - Stale - OTC Variation
    When Associated data is No
    AND
    today >= Effective stale date due to OTC effective date
    NB: Associated data is Yes IF
    (last modified date >= Association date due to OTC effective date
    OR Operating period start date = OTC effective date).
    """
    otc_service = ServiceModelFactory(effective_date=date.fromisoformat(effective))
    txc = TXCFileAttributesFactory(
        licence_number=otc_service.licence.number,
        service_code=otc_service.registration_number.replace("/", ":"),
        modification_datetime=datetime.fromisoformat(modified + "T00:00:00+00:00"),
        operating_period_start_date=period_start
        if period_end is None
        else date.fromisoformat(period_end) - timedelta(days=100),
        operating_period_end_date=None
        if period_end is None
        else date.fromisoformat(period_end),
    )
    DataQualityReportFactory(revision=txc.revision)
    PTIValidationResultFactory(revision=txc.revision)
    LicenceFactory(number=otc_service.licence.number)

    df = _get_timetable_catalogue_dataframe()
    assert (df["Staleness Status"][0] == "Stale - OTC Variation") == is_stale
    assert df["Requires Attention"][0] == "Yes" if is_stale else "No"


@freeze_time("2023-02-14")
def test_not_stale():
    """
    Staleness Status - Not Stale
    Default status for service codes published to BODS
    """
    effective = "2022-11-01"
    modified = "2023-01-01"
    period_end = "2023-09-01"
    otc_service = ServiceModelFactory(effective_date=date.fromisoformat(effective))
    txc = TXCFileAttributesFactory(
        licence_number=otc_service.licence.number,
        service_code=otc_service.registration_number.replace("/", ":"),
        modification_datetime=datetime.fromisoformat(modified + "T00:00:00+00:00"),
        operating_period_start_date=None
        if period_end is None
        else date.fromisoformat(period_end) - timedelta(days=100),
        operating_period_end_date=None
        if period_end is None
        else date.fromisoformat(period_end),
    )
    DataQualityReportFactory(revision=txc.revision)
    PTIValidationResultFactory(revision=txc.revision)
    LicenceFactory(number=otc_service.licence.number)

    df = _get_timetable_catalogue_dataframe()
    assert df["Staleness Status"][0] == "Not Stale"
    assert df["Requires Attention"][0] == "No"


@freeze_time("2023-02-14")
def test_stale_service_out_of_season():
    # Set conditions that would mean the service was stale due to end date
    # passed if it were in season
    effective = "2022-01-01"
    modified = "2022-06-01"
    period_end = "2023-03-01"
    # Set the service as currently out of season
    seasonal_start = "2022-11-01"
    seasonal_end = "2023-01-01"

    otc_service = ServiceModelFactory(effective_date=date.fromisoformat(effective))
    txc = TXCFileAttributesFactory(
        licence_number=otc_service.licence.number,
        service_code=otc_service.registration_number.replace("/", ":"),
        modification_datetime=datetime.fromisoformat(modified + "T00:00:00+00:00"),
        operating_period_start_date=None
        if period_end is None
        else date.fromisoformat(period_end) - timedelta(days=100),
        operating_period_end_date=None
        if period_end is None
        else date.fromisoformat(period_end),
    )
    DataQualityReportFactory(revision=txc.revision)
    PTIValidationResultFactory(revision=txc.revision)
    bods_licence = LicenceFactory(number=otc_service.licence.number)

    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=otc_service.registration_code,
        start=date.fromisoformat(seasonal_start),
        end=date.fromisoformat(seasonal_end),
    )

    df = _get_timetable_catalogue_dataframe()
    assert df["Staleness Status"][0] == "Stale - 42 day look ahead"
    assert df["Seasonal Status"][0] == "Out of Season"
    assert df["Requires Attention"][0] == "No"
