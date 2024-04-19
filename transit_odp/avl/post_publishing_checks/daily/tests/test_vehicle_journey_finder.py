import datetime
from pathlib import Path

import pytest

from transit_odp.avl.post_publishing_checks.constants import ErrorCategory
from transit_odp.avl.post_publishing_checks.daily.results import ValidationResult
from transit_odp.avl.post_publishing_checks.daily.vehicle_journey_finder import (
    DayOfWeek,
    TxcVehicleJourney,
    VehicleJourneyFinder,
)
from transit_odp.avl.post_publishing_checks.models import MonitoredVehicleJourney
from transit_odp.organisation.factories import DatasetFactory, TXCFileAttributesFactory
from transit_odp.organisation.models import TXCFileAttributes
from transit_odp.timetables.transxchange import TransXChangeDocument

pytestmark = pytest.mark.django_db

DATA_DIR = Path(__file__).parent / "data"


def test_get_txc_file_metadata():
    TXCFileAttributesFactory(national_operator_code="NOC1", line_names=["L1", "L2"])
    txc_file_attrs = TXCFileAttributesFactory(
        national_operator_code="NOC1", line_names=["L3", "L4"]
    )
    TXCFileAttributesFactory(national_operator_code="NOC2", line_names=["L3", "L4"])
    TXCFileAttributesFactory(national_operator_code="NOC2", line_names=["L1", "L2"])

    vehicle_journey_finder = VehicleJourneyFinder()
    txc_file_list = vehicle_journey_finder.get_txc_file_metadata(
        noc="NOC1", published_line_name="L4", result=ValidationResult()
    )
    assert len(txc_file_list) == 1
    assert txc_file_list[0].id == txc_file_attrs.id


def test_check_same_dataset_succeeds():
    dataset = DatasetFactory()
    TXCFileAttributesFactory.create_batch(5, revision__dataset=dataset)
    txc_file_attrs = list(TXCFileAttributes.objects.add_revision_details())
    mvj = MonitoredVehicleJourney(operator_ref="Itoworld", vehicle_ref="Bertha")
    vehicle_journey_finder = VehicleJourneyFinder()
    consistent = vehicle_journey_finder.check_same_dataset(
        txc_file_attrs, mvj, ValidationResult()
    )
    assert consistent


def test_check_same_dataset_fails():
    datasets = DatasetFactory.create_batch(2)
    TXCFileAttributesFactory.create_batch(3, revision__dataset=datasets[0])
    TXCFileAttributesFactory.create_batch(2, revision__dataset=datasets[1])
    txc_file_attrs = list(TXCFileAttributes.objects.add_revision_details())
    mvj = MonitoredVehicleJourney(operator_ref="Itoworld", vehicle_ref="Bertha")
    vehicle_journey_finder = VehicleJourneyFinder()
    consistent = vehicle_journey_finder.check_same_dataset(
        txc_file_attrs, mvj, ValidationResult()
    )
    assert not consistent


def test_filter_by_operating_period():
    txc_filenames = [
        str(DATA_DIR / xml)
        for xml in ("current_year.xml", "next_year.xml", "current_year_no_end_date.xml")
    ]
    txc_xml = [TransXChangeDocument(f) for f in txc_filenames]
    activity_date = datetime.date.fromisoformat("2022-12-01")
    result = ValidationResult()
    vehicle_journey_finder = VehicleJourneyFinder()
    vehicle_journey_finder.filter_by_operating_period(activity_date, txc_xml, result)

    assert len(txc_xml) == 2
    assert txc_xml[0].get_file_name() == "current_year.xml"
    assert txc_xml[1].get_file_name() == "current_year_no_end_date.xml"


def test_filter_by_journey_code():
    txc_filenames = [
        str(DATA_DIR / xml)
        for xml in (
            "current_year.xml",
            "next_year.xml",
            "current_year_no_end_date.xml",
            "vehicle_journeys.xml",
        )
    ]
    txc_xml = [TransXChangeDocument(f) for f in txc_filenames]
    vehicle_journey_ref = "50"
    vehicle_journey_finder = VehicleJourneyFinder()
    txc_vehicle_journey = vehicle_journey_finder.filter_by_journey_code(
        txc_xml, vehicle_journey_ref, ValidationResult()
    )

    assert len(txc_vehicle_journey) == 1
    assert txc_vehicle_journey[0].vehicle_journey["SequenceNumber"] == "2"
    assert txc_vehicle_journey[0].txc_xml.get_file_name() == "vehicle_journeys.xml"


@pytest.mark.parametrize(
    "sequence_number,expected_days",
    [
        ("1", [DayOfWeek.monday, DayOfWeek.friday]),
        ("2", [DayOfWeek.tuesday]),
    ],
)
def test_get_operating_profile_for_journey(sequence_number, expected_days):
    txc_filename = str(DATA_DIR / "vehicle_journeys.xml")
    txc_xml = TransXChangeDocument(txc_filename)
    vehicle_journey = [
        vj
        for vj in txc_xml.get_vehicle_journeys()
        if vj["SequenceNumber"] == sequence_number
    ]

    txc_vehicle_journey = TxcVehicleJourney(vehicle_journey[0], txc_xml)
    vehicle_journey_finder = VehicleJourneyFinder()
    profile = vehicle_journey_finder.get_operating_profile_for_journey(
        txc_vehicle_journey
    )

    days_of_week = profile.get_element("RegularDayType").get_element("DaysOfWeek")
    days_found = []
    for day in DayOfWeek:
        if days_of_week.get_element_or_none(day.value) is not None:
            days_found.append(day)
    assert days_found == expected_days


def test_filter_by_operating_profile():
    txc_filename = str(DATA_DIR / "vehicle_journeys.xml")
    txc_xml = TransXChangeDocument(txc_filename)
    vehicle_journeys = txc_xml.get_vehicle_journeys()
    txc_vehicle_journeys = [TxcVehicleJourney(vj, txc_xml) for vj in vehicle_journeys]
    # Set activity date to a Tuesday
    activity_date = datetime.date.fromisoformat("2022-01-04")
    vehicle_journey_finder = VehicleJourneyFinder()
    vehicle_journey_finder.filter_by_operating_profile(
        activity_date, txc_vehicle_journeys, ValidationResult()
    )

    assert len(txc_vehicle_journeys) == 1
    assert txc_vehicle_journeys[0].vehicle_journey["SequenceNumber"] == "2"


def test_filter_by_revision_number():
    txc_filenames = [
        str(DATA_DIR / xml)
        for xml in (
            "vehicle_journeys.xml",
            "vehicle_journeys2.xml",
            "vehicle_journeys3.xml",
        )
    ]
    txc_xml = [TransXChangeDocument(f) for f in txc_filenames]
    txc_vehicle_journeys = [
        TxcVehicleJourney(txc.get_vehicle_journeys()[0], txc) for txc in txc_xml
    ]
    vehicle_journey_finder = VehicleJourneyFinder()
    vehicle_journey_finder.filter_by_revision_number(
        txc_vehicle_journeys, ValidationResult()
    )

    assert len(txc_vehicle_journeys) == 2
    assert txc_vehicle_journeys[0].vehicle_journey["SequenceNumber"] == "200"
    assert txc_vehicle_journeys[1].vehicle_journey["SequenceNumber"] == "300"
    assert txc_vehicle_journeys[0].txc_xml.get_revision_number() == "2"
    assert txc_vehicle_journeys[1].txc_xml.get_revision_number() == "2"


def test_filter_by_days_of_operation():
    txc_filename = str(DATA_DIR / "vehicle_journeys4.xml")
    txc_xml = TransXChangeDocument(txc_filename)
    vehicle_journeys = txc_xml.get_vehicle_journeys()
    txc_vehicle_journeys = [TxcVehicleJourney(vj, txc_xml) for vj in vehicle_journeys]
    # Set recorded at date within serviced org working days
    recorded_at_time = datetime.date.fromisoformat("2023-04-18")
    vehicle_journey_finder = VehicleJourneyFinder()
    vehicle_journey_finder.filter_by_days_of_operation(
        recorded_at_time, txc_vehicle_journeys, ValidationResult()
    )

    assert len(txc_vehicle_journeys) == 1
    assert txc_vehicle_journeys[0].vehicle_journey["SequenceNumber"] == "1"


def test_filter_by_days_of_operation_service_inherited():
    txc_filename = str(DATA_DIR / "vehicle_journeys7.xml")
    txc_xml = TransXChangeDocument(txc_filename)
    vehicle_journeys = txc_xml.get_vehicle_journeys()
    txc_vehicle_journeys = [TxcVehicleJourney(vj, txc_xml) for vj in vehicle_journeys]
    # Set recorded at date within serviced org working days
    recorded_at_time = datetime.date.fromisoformat("2023-04-18")
    vehicle_journey_finder = VehicleJourneyFinder()
    vehicle_journey_finder.filter_by_days_of_operation(
        recorded_at_time, txc_vehicle_journeys, ValidationResult()
    )

    assert len(txc_vehicle_journeys) == 1
    assert txc_vehicle_journeys[0].vehicle_journey["SequenceNumber"] == "1"


def test_filter_by_days_of_operation_missing_operating_profile_element():
    txc_filename = str(DATA_DIR / "vehicle_journeys8.xml")
    txc_xml = TransXChangeDocument(txc_filename)
    vehicle_journeys = txc_xml.get_vehicle_journeys()
    txc_vehicle_journeys = [TxcVehicleJourney(vj, txc_xml) for vj in vehicle_journeys]
    # Set recorded at date within serviced org working days
    recorded_at_time = datetime.date.fromisoformat("2023-04-18")
    vehicle_journey_finder = VehicleJourneyFinder()
    vehicle_journey_finder.filter_by_days_of_operation(
        recorded_at_time, txc_vehicle_journeys, ValidationResult()
    )

    assert len(txc_vehicle_journeys) == 2
    assert txc_vehicle_journeys[0].vehicle_journey["SequenceNumber"] == "1"


@pytest.mark.parametrize(
    "txc_files,expected_result,expected_error",
    [
        (
            ["vehicle_journeys5.xml"],
            False,
            [
                "Found more than one matching vehicle journey in timetables belonging to a single service code"
            ],
        ),
        (["vehicle_journeys5.xml", "vehicle_journeys6.xml"], False, None),
        (
            ["vehicle_journeys4.xml", "vehicle_journeys5.xml"],
            False,
            [
                "Found more than one matching vehicle journey in timetables belonging to a single service code"
            ],
        ),
    ],
)
def test_filter_by_service_code(txc_files, expected_result, expected_error):
    txc_filenames = [str(DATA_DIR / xml) for xml in txc_files]
    txc_xml = [TransXChangeDocument(f) for f in txc_filenames]
    txc_vehicle_journeys = [
        TxcVehicleJourney(txc.get_vehicle_journeys()[0], txc) for txc in txc_xml
    ]
    vehicle_journey_finder = VehicleJourneyFinder()
    result = ValidationResult()
    return_result = vehicle_journey_finder.filter_by_service_code(
        txc_vehicle_journeys, result
    )

    assert return_result == expected_result
    if result.errors is not None:
        assert result.errors[ErrorCategory.GENERAL] == expected_error
    else:
        assert result.errors == expected_error


def test_filter_by_published_line_name():
    txc_filenames = [
        str(DATA_DIR / xml) for xml in ("vehicle_journeys_same_journey_code.xml",)
    ]
    txc_xml = [TransXChangeDocument(f) for f in txc_filenames]
    txc_vehicle_journeys = [
        TxcVehicleJourney(txc.get_vehicle_journeys()[0], txc) for txc in txc_xml
    ]
    filter_published_line_name = "695"
    result = ValidationResult()
    vehicle_journey_finder = VehicleJourneyFinder()
    txc_vehicle_journey = vehicle_journey_finder.filter_by_published_line_name(
        txc_vehicle_journeys,
        published_line_name=filter_published_line_name,
        result=result,
    )
    assert len(txc_vehicle_journey) == 1
    assert txc_vehicle_journey[0].vehicle_journey["SequenceNumber"] == "1"


def test_filter_by_published_line_name_no_matching_lineref():
    txc_filenames = [
        str(DATA_DIR / xml) for xml in ("vehicle_journeys_no_matching_lineref.xml",)
    ]
    txc_xml = [TransXChangeDocument(f) for f in txc_filenames]
    txc_vehicle_journeys = [
        TxcVehicleJourney(txc.get_vehicle_journeys()[0], txc) for txc in txc_xml
    ]
    filter_published_line_name = "695"
    result = ValidationResult()
    vehicle_journey_finder = VehicleJourneyFinder()
    txc_vehicle_journey = vehicle_journey_finder.filter_by_published_line_name(
        txc_vehicle_journeys,
        published_line_name=filter_published_line_name,
        result=result,
    )
    assert result.errors[ErrorCategory.GENERAL] == [
        "No published TxC files found with vehicle journey LineRef that matches with the PublishedLineName"
    ]
    assert txc_vehicle_journey is None
