from datetime import date, datetime, timedelta

import pytest
import numpy as np
from factory import Sequence
from freezegun import freeze_time

from transit_odp.data_quality.factories import (
    DataQualityReportFactory,
    PTIValidationResultFactory,
)
from transit_odp.naptan.factories import AdminAreaFactory
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
from transit_odp.otc.factories import (
    LicenceModelFactory,
    LocalAuthorityFactory,
    ServiceModelFactory,
    UILtaFactory,
)
from transit_odp.otc.models import Service
from transit_odp.timetables.csv import _get_timetable_line_level_catalogue_dataframe

pytestmark = pytest.mark.django_db


def test_csv_output_order():
    """
    Test the order of the headers in the column.
    """
    for service in ServiceModelFactory.create_batch(5):
        fa = TXCFileAttributesFactory(
            licence_number=service.licence.number,
            service_code=service.registration_number.replace("/", ":"),
            line_names=[service.service_number],
        )
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)

    df = _get_timetable_line_level_catalogue_dataframe()
    columns = df.columns

    assert columns[0] == "Registration:Registration Number"
    assert columns[1] == "Registration:Service Number"
    assert columns[2] == "Requires Attention"
    assert columns[3] == "Published Status"
    assert columns[4] == "Registration Status"
    assert columns[5] == "Scope Status"
    assert columns[6] == "Seasonal Status"
    assert columns[7] == "Timeliness Status"
    assert columns[8] == "Organisation Name"
    assert columns[9] == "Data set ID"
    assert columns[10] == "XML:Filename"
    assert columns[11] == "XML:Last Modified Date"
    assert columns[12] == "XML:Operating Period End Date"
    assert columns[13] == "Date Registration variation needs to be published"
    assert columns[14] == "Date for complete 42 day look ahead"
    assert columns[15] == "Date when data is over 1 year old"
    assert columns[16] == "Date seasonal service should be published"
    assert columns[17] == "Seasonal Start Date"
    assert columns[18] == "Seasonal End Date"
    assert columns[19] == "Registration:Operator Name"
    assert columns[20] == "Registration:Licence Number"
    assert columns[21] == "Registration:Service Type Description"
    assert columns[22] == "Registration:Variation Number"
    assert columns[23] == "Registration:Expiry Date"
    assert columns[24] == "Registration:Effective Date"
    assert columns[25] == "Registration:Received Date"
    assert columns[26] == "Traveline Region"
    assert columns[27] == "Local Transport Authority"


def test_service_in_bods_but_not_in_otc():
    for fa in TXCFileAttributesFactory.create_batch(
        5, service_code=Sequence(lambda n: f"PD00000{n}")
    ):
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)

    services = ServiceModelFactory.create_batch(5)
    ui_lta = UILtaFactory(name="Dorset County Council")
    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=services,
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    df = _get_timetable_line_level_catalogue_dataframe()

    assert len(df) == 5
    for index, row in df.iterrows():
        assert row["Published Status"] == "Unpublished"
        assert row["Registration Status"] == "Registered"
        assert row["Scope Status"] == "In Scope"


def test_service_in_bods_and_otc():
    import datetime

    services = ServiceModelFactory.create_batch(5)
    for service in services:
        fa = TXCFileAttributesFactory(
            licence_number=service.licence.number,
            service_code=service.registration_number.replace("/", ":"),
            line_names=[service.service_number],
        )
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)

    ui_lta = UILtaFactory(name="Dorset County Council")
    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=services,
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    df = _get_timetable_line_level_catalogue_dataframe()
    for index, row in df.iterrows():
        dataset = Dataset.objects.get(id=row["Data set ID"])
        service = Service.objects.get(
            registration_number=row["Registration:Registration Number"]
        )
        operator = service.operator
        licence = service.licence
        txc_file_attributes = dataset.live_revision.txc_file_attributes.first()
        date_OTC_variation_published = service.effective_date - timedelta(days=42)
        date_complete_42_day_look_ahead = datetime.date.today() + timedelta(days=42)

        assert row["Registration:Registration Number"] == service.registration_number
        assert row["Registration:Service Number"] == service.service_number
        assert row["Requires Attention"] == "Yes"
        assert row["Published Status"] == "Published"
        assert row["Registration Status"] == "Registered"
        assert row["Scope Status"] == "In Scope"
        assert row["Seasonal Status"] == "Not Seasonal"
        assert row["Timeliness Status"] == "OTC variation not published"
        assert row["Data set ID"] == dataset.id
        assert (
            row["Date Registration variation needs to be published"]
            == date_OTC_variation_published
        )
        assert (
            row["Date for complete 42 day look ahead"].to_pydatetime().date()
            == date_complete_42_day_look_ahead
        )
        assert row["XML:Filename"] == txc_file_attributes.filename
        assert (
            row["XML:Last Modified Date"]
            == (txc_file_attributes.modification_datetime).date()
        )
        assert (
            row["XML:Operating Period End Date"]
            == txc_file_attributes.operating_period_end_date
        )
        assert row["Registration:Operator Name"] == operator.operator_name
        assert row["Registration:Licence Number"] == licence.number
        assert (
            row["Registration:Service Type Description"]
            == service.service_type_description
        )
        assert row["Registration:Variation Number"] == service.variation_number
        assert row["Registration:Expiry Date"] == licence.expiry_date
        assert row["Registration:Effective Date"] == service.effective_date
        assert row["Registration:Received Date"] == service.received_date


def test_service_in_otc_and_not_in_bods():
    licence_number = "PD0000099"
    org_name = "test_org_1"
    org1 = OrganisationFactory(name=org_name)
    LicenceFactory(organisation=org1, number=licence_number)
    otc_lic = LicenceModelFactory(id=10, number=licence_number)
    service = ServiceModelFactory(licence=otc_lic)
    TXCFileAttributesFactory()
    ui_lta = UILtaFactory(name="Dorset County Council")
    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=[service],
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    df = _get_timetable_line_level_catalogue_dataframe()

    for _, row in df[1:].iterrows():
        service = Service.objects.get(
            registration_number=row["Registration:Registration Number"]
        )
        operator = service.operator
        licence = service.licence

        assert row["Published Status"] == "Unpublished"
        assert row["Registration Status"] == "Registered"
        assert row["Scope Status"] == "In Scope"
        assert row["Registration:Operator Name"] == operator.operator_name
        assert row["Registration:Licence Number"] == licence.number
        assert row["Registration:Registration Number"] == service.registration_number
        assert row["Registration:Service Number"] == service.service_number
        assert row["Registration:Expiry Date"] == licence.expiry_date
        assert row["Registration:Effective Date"] == service.effective_date
        assert row["Registration:Received Date"] == service.received_date
        assert row["Requires Attention"] == "Yes"
        assert row["Organisation Name"] == org_name


def test_service_in_otc_and_not_in_bods_no_organisation_name_created():
    ServiceModelFactory.create_batch(5)
    TXCFileAttributesFactory.create_batch(5)

    df = _get_timetable_line_level_catalogue_dataframe()
    for _, row in df.iterrows():
        assert row["Published Status"] == "Unpublished"
        assert row["Organisation Name"] == "Organisation not yet created"


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
            line_names=[service.service_number],
        )
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)
        bods_lic = LicenceFactory(number=service.licence.number)
        ServiceCodeExemptionFactory(
            licence=bods_lic, registration_code=service.registration_code
        )

    df = _get_timetable_line_level_catalogue_dataframe()
    for _, row in df.iterrows():
        assert row["Published Status"] == "Published"
        assert row["Registration Status"] == "Registered"
        assert row["Scope Status"] == "Out of Scope"


def test_empty_otc_services():
    for fa in TXCFileAttributesFactory.create_batch(
        5, service_code=Sequence(lambda n: f"UZ00000{n}")
    ):
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)

    with pytest.raises(EmptyDataFrame):
        _get_timetable_line_level_catalogue_dataframe()


def test_empty_txc_services():
    ServiceModelFactory.create_batch(5)

    with pytest.raises(EmptyDataFrame):
        _get_timetable_line_level_catalogue_dataframe()


def test_duplicated_txc_services():
    for service in ServiceModelFactory.create_batch(5):
        fa = TXCFileAttributesFactory.create_batch(
            2,
            licence_number=service.licence.number,
            service_code=service.registration_number.replace("/", ":"),
            line_names=[service.service_number],
        )[0]
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)

    df = _get_timetable_line_level_catalogue_dataframe()
    assert len(df) == 5


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
        line_names=[otc_service.service_number],
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

    df = _get_timetable_line_level_catalogue_dataframe()
    assert df["Seasonal Status"][0] == status
    if start and end is not None:
        assert (
            df["Seasonal Start Date"][0] == datetime.strptime(start, "%Y-%m-%d").date()
        )
        assert df["Seasonal End Date"][0] == datetime.strptime(end, "%Y-%m-%d").date()
        assert df["Date seasonal service should be published"][0] == df[
            "Seasonal Start Date"
        ][0] - timedelta(days=42)


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
    Timeliness Status - 42 day look ahead is incomplete
    If “Effective stale date due to end date” (if present)  is sooner than
    “Effective stale date due to effective last modified date”
    and today's date from which the file is created equals or passes
    “Effective stale date due to end date”
    and Last modified date < OTC Effective start date - FALSE
    """
    otc_service = ServiceModelFactory(effective_date=date.fromisoformat(effective))
    txc = TXCFileAttributesFactory(
        licence_number=otc_service.licence.number,
        service_code=otc_service.registration_number.replace("/", ":"),
        line_names=[otc_service.service_number],
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
    ui_lta = UILtaFactory(name="Dorset County Council")
    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=[otc_service],
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    df = _get_timetable_line_level_catalogue_dataframe()
    assert (df["Timeliness Status"][0] == "42 day look ahead is incomplete") == is_stale
    assert df["Requires Attention"][0] == "Yes" if is_stale else "No"


@freeze_time("2023-02-14")
@pytest.mark.parametrize(
    "effective, modified, period_end, period_start, is_stale",
    (
        # All conditions satisfied for staleness
        ("2021-12-01", "2022-01-01", "2023-06-01", None, True),
        # End date not present
        ("2021-12-01", "2022-01-01", None, None, True),
        # 42 days look ahead is true
        ("2022-01-01", "2023-06-01", "2023-03-01", None, False),
        # OTC variation is true
        ("2023-03-01", "2023-12-01", "2025-01-01", "2023-01-01", False),
        # today is equal to last modified date + 365 days
        ("2022-01-01", "2022-02-14", "2023-06-01", None, True),
        # 1 days short to be marked as 12 months stale
        ("2022-01-01", "2022-02-15", "2023-06-01", None, False),
    ),
)
def test_stale_12_months_old(effective, modified, period_end, period_start, is_stale):
    """
    Timeliness Status - Service hasn’t been updated within a year
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
        line_names=[otc_service.service_number],
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
    ui_lta = UILtaFactory(name="Dorset County Council")
    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=[otc_service],
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    df = _get_timetable_line_level_catalogue_dataframe()
    assert (
        df["Timeliness Status"][0] == "Service hasn't been updated within a year"
    ) == is_stale
    assert df["Requires Attention"][0] == "Yes" if is_stale else "No"
    assert (
        df["Date when data is over 1 year old"][0]
        == txc.modification_datetime.replace(
            year=txc.modification_datetime.year + 1
        ).date()
    )


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
    Timeliness Status - OTC variation not published
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
        line_names=[otc_service.service_number],
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
    ui_lta = UILtaFactory(name="Dorset County Council")
    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=[otc_service],
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    df = _get_timetable_line_level_catalogue_dataframe()
    assert (df["Timeliness Status"][0] == "OTC variation not published") == is_stale
    assert df["Requires Attention"][0] == "Yes" if is_stale else "No"


@freeze_time("2023-02-14")
def test_not_stale():
    """
    Timeliness Status - Up to date
    Default status for service codes published to BODS
    """
    effective = "2022-11-01"
    modified = "2023-01-01"
    period_end = "2023-09-01"
    otc_service = ServiceModelFactory(effective_date=date.fromisoformat(effective))
    txc = TXCFileAttributesFactory(
        licence_number=otc_service.licence.number,
        service_code=otc_service.registration_number.replace("/", ":"),
        line_names=[otc_service.service_number],
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

    df = _get_timetable_line_level_catalogue_dataframe()
    assert df["Timeliness Status"][0] == "Up to date"
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
        line_names=[otc_service.service_number],
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

    df = _get_timetable_line_level_catalogue_dataframe()
    assert df["Timeliness Status"][0] == "42 day look ahead is incomplete"
    assert df["Seasonal Status"][0] == "Out of Season"
    assert df["Requires Attention"][0] == "No"
