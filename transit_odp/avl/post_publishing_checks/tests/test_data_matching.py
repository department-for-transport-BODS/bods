from pathlib import Path

import pytest

from transit_odp.avl.post_publishing_checks.constants import SirivmField
from transit_odp.avl.post_publishing_checks.data_matching import DataMatching
from transit_odp.avl.post_publishing_checks.models import MonitoredVehicleJourney
from transit_odp.avl.post_publishing_checks.results import (
    ErrorCategory,
    ValidationResult,
)
from transit_odp.avl.post_publishing_checks.vehicle_journey_finder import (
    TxcVehicleJourney,
)
from transit_odp.timetables.transxchange import (
    TransXChangeDocument,
    TransXChangeElement,
)

pytestmark = pytest.mark.django_db

DATA_DIR = Path(__file__).parent / "data"


def get_txc_vehicle_journey(filename: str, sequence_number: str) -> TxcVehicleJourney:
    txc_filename = str(DATA_DIR / filename)
    txc_xml = TransXChangeDocument(txc_filename)
    vehicle_journeys = txc_xml.get_vehicle_journeys()
    for vj in vehicle_journeys:
        if vj["SequenceNumber"] == sequence_number:
            return TxcVehicleJourney(vj, txc_xml)
    assert (
        False
    ), f"No VehicleJourney with SequenceNumber {sequence_number} in {filename}"


@pytest.mark.parametrize(
    "mvj_direction_ref,filename,sequence_number,txc_direction",
    [
        ("outbound", "vehicle_journeys.xml", "1", "outbound"),
        ("outbound", "vehicle_journeys.xml", "2", "inboundAndOutbound"),
        ("INBOUND", "vehicle_journeys.xml", "3", "inbound"),
        ("inbound", "vehicle_journeys.xml", "2", "inboundAndOutbound"),
        ("clockwise", "vehicle_journeys.xml", "4", "clockwise"),
        ("clockwise", "vehicle_journeys.xml", "5", "circular"),
        ("anticlockwise", "vehicle_journeys.xml", "6", "anticlockwise"),
        ("ANTICLOCKWISE", "vehicle_journeys.xml", "5", "circular"),
    ],
)
def test_data_match_direction_ref_succeeds(
    mvj_direction_ref, filename, sequence_number, txc_direction
):
    mvj = MonitoredVehicleJourney(
        direction_ref=mvj_direction_ref, operator_ref="Itoworld", vehicle_ref="Bertha"
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename=filename, sequence_number=sequence_number
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_direction_ref(mvj, txc_vehicle_journey, result)

    assert result.sirivm_value(SirivmField.DIRECTION_REF) == mvj_direction_ref
    assert result.txc_value(SirivmField.DIRECTION_REF) == txc_direction
    assert result.matches(SirivmField.DIRECTION_REF)
    assert len(result.errors.get(ErrorCategory.DIRECTION_REF)) == 0


@pytest.mark.parametrize(
    "mvj_direction_ref,filename,sequence_number,txc_direction",
    [
        (None, "vehicle_journeys.xml", "1", None),
        ("north", "vehicle_journeys.xml", "1", None),
        ("inbound", "vehicle_journeys.xml", "7", None),
        ("inbound", "vehicle_journeys.xml", "1", "outbound"),
    ],
)
def test_data_match_direction_ref_errors(
    mvj_direction_ref, filename, sequence_number, txc_direction
):
    mvj = MonitoredVehicleJourney(
        direction_ref=mvj_direction_ref, operator_ref="Itoworld", vehicle_ref="Bertha"
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename=filename, sequence_number=sequence_number
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_direction_ref(mvj, txc_vehicle_journey, result)

    assert result.sirivm_value(SirivmField.DIRECTION_REF) == mvj_direction_ref
    assert result.txc_value(SirivmField.DIRECTION_REF) == txc_direction
    assert not result.matches(SirivmField.DIRECTION_REF)
    assert len(result.errors.get(ErrorCategory.DIRECTION_REF)) > 0


def test_data_match_block_ref_succeeds():
    mvj_block_ref = "Jenny"
    mvj = MonitoredVehicleJourney(
        block_ref=mvj_block_ref, operator_ref="Itoworld", vehicle_ref="Bertha"
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename="vehicle_journeys.xml", sequence_number="1"
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_block_ref(mvj, txc_vehicle_journey, result)

    assert result.sirivm_value(SirivmField.BLOCK_REF) == mvj_block_ref
    assert result.txc_value(SirivmField.BLOCK_REF) == mvj_block_ref
    assert result.matches(SirivmField.BLOCK_REF)
    assert len(result.errors.get(ErrorCategory.BLOCK_REF)) == 0


@pytest.mark.parametrize(
    "mvj_block_ref,filename,sequence_number,txc_block_number",
    [
        (None, "vehicle_journeys.xml", "1", None),
        ("Jenny", "vehicle_journeys.xml", "2", None),
        ("Jenny", "vehicle_journeys.xml", "3", "Lopez"),
    ],
)
def test_data_match_block_ref_errors(
    mvj_block_ref, filename, sequence_number, txc_block_number
):
    mvj = MonitoredVehicleJourney(
        block_ref=mvj_block_ref, operator_ref="Itoworld", vehicle_ref="Bertha"
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename=filename, sequence_number=sequence_number
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_block_ref(mvj, txc_vehicle_journey, result)

    assert result.sirivm_value(SirivmField.BLOCK_REF) == mvj_block_ref
    assert result.txc_value(SirivmField.BLOCK_REF) == txc_block_number
    assert not result.matches(SirivmField.BLOCK_REF)
    assert len(result.errors.get(ErrorCategory.BLOCK_REF)) > 0


def test_data_match_published_line_name_succeeds():
    mvj_published_line_name = "Piccadilly"
    mvj = MonitoredVehicleJourney(
        published_line_name=mvj_published_line_name,
        operator_ref="Itoworld",
        vehicle_ref="Bertha",
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename="vehicle_journeys.xml", sequence_number="1"
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_published_line_name(mvj, txc_vehicle_journey, result)

    assert (
        result.sirivm_value(SirivmField.PUBLISHED_LINE_NAME) == mvj_published_line_name
    )
    assert result.txc_value(SirivmField.PUBLISHED_LINE_NAME) == mvj_published_line_name
    assert result.matches(SirivmField.PUBLISHED_LINE_NAME)
    assert len(result.errors.get(ErrorCategory.PUBLISHED_LINE_NAME)) == 0


@pytest.mark.parametrize(
    "mvj_published_line_name,filename,sequence_number,txc_line_name",
    [
        (None, "vehicle_journeys.xml", "1", None),
        ("Victoria", "vehicle_journeys.xml", "2", None),
        ("Victoria", "vehicle_journeys.xml", "3", None),
        ("Victoria", "vehicle_journeys.xml", "1", "Piccadilly"),
    ],
)
def test_data_match_published_line_name_errors(
    mvj_published_line_name, filename, sequence_number, txc_line_name
):
    mvj = MonitoredVehicleJourney(
        published_line_name=mvj_published_line_name,
        operator_ref="Itoworld",
        vehicle_ref="Bertha",
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename=filename, sequence_number=sequence_number
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_published_line_name(mvj, txc_vehicle_journey, result)

    assert (
        result.sirivm_value(SirivmField.PUBLISHED_LINE_NAME) == mvj_published_line_name
    )
    assert result.txc_value(SirivmField.PUBLISHED_LINE_NAME) == txc_line_name
    assert not result.matches(SirivmField.PUBLISHED_LINE_NAME)
    assert len(result.errors.get(ErrorCategory.PUBLISHED_LINE_NAME)) > 0


def test_get_journey_pattern_and_section_refs():
    txc_filename = str(DATA_DIR / "vehicle_journeys.xml")
    txc_xml = TransXChangeDocument(txc_filename)
    vehicle_journey = [
        vj for vj in txc_xml.get_vehicle_journeys() if vj["SequenceNumber"] == "2"
    ]
    vj = TxcVehicleJourney(vehicle_journey[0], txc_xml)

    data_matching = DataMatching()
    (
        jp,
        jp_section_refs,
    ) = data_matching.get_journey_pattern_and_section_refs_from_vehicle_journey(vj)
    assert type(jp) == TransXChangeElement
    assert jp["id"] == "JP6"
    assert len(jp_section_refs) == 2
    assert jp_section_refs[0].text == "JPS61"
    assert jp_section_refs[1].text == "JPS62"


def test_data_match_destination_ref_succeeds():
    mvj_destination_ref = "Pluto"
    mvj = MonitoredVehicleJourney(
        destination_ref=mvj_destination_ref,
        operator_ref="Itoworld",
        vehicle_ref="Bertha",
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename="vehicle_journeys.xml", sequence_number="1"
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_destination_ref(mvj, txc_vehicle_journey, result)

    assert result.sirivm_value(SirivmField.DESTINATION_REF) == mvj_destination_ref
    assert result.txc_value(SirivmField.DESTINATION_REF) == mvj_destination_ref
    assert result.matches(SirivmField.DESTINATION_REF)
    assert len(result.errors.get(ErrorCategory.DESTINATION_REF)) == 0


@pytest.mark.parametrize(
    "mvj_destination_ref,filename,sequence_number,txc_stop_point",
    [
        (None, "vehicle_journeys.xml", "1", None),
        ("Saturn", "vehicle_journeys.xml", "2", None),
        ("Saturn", "vehicle_journeys.xml", "3", None),
        ("Saturn", "vehicle_journeys.xml", "1", "Pluto"),
    ],
)
def test_data_match_destination_ref_errors(
    mvj_destination_ref, filename, sequence_number, txc_stop_point
):
    mvj = MonitoredVehicleJourney(
        destination_ref=mvj_destination_ref,
        operator_ref="Itoworld",
        vehicle_ref="Bertha",
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename=filename, sequence_number=sequence_number
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_destination_ref(mvj, txc_vehicle_journey, result)

    assert result.sirivm_value(SirivmField.DESTINATION_REF) == mvj_destination_ref
    assert result.txc_value(SirivmField.DESTINATION_REF) == txc_stop_point
    assert not result.matches(SirivmField.DESTINATION_REF)
    assert len(result.errors.get(ErrorCategory.DESTINATION_REF)) > 0


def test_data_match_origin_ref_succeeds():
    mvj_origin_ref = "Earth"
    mvj = MonitoredVehicleJourney(
        origin_ref=mvj_origin_ref,
        operator_ref="Itoworld",
        vehicle_ref="Bertha",
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename="vehicle_journeys.xml", sequence_number="1"
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_origin_ref(mvj, txc_vehicle_journey, result)

    assert result.sirivm_value(SirivmField.ORIGIN_REF) == mvj_origin_ref
    assert result.txc_value(SirivmField.ORIGIN_REF) == mvj_origin_ref
    assert result.matches(SirivmField.ORIGIN_REF)
    assert len(result.errors.get(ErrorCategory.ORIGIN_REF)) == 0


@pytest.mark.parametrize(
    "mvj_origin_ref,filename,sequence_number,txc_stop_point",
    [
        (None, "vehicle_journeys.xml", "1", None),
        ("Saturn", "vehicle_journeys.xml", "2", None),
        ("Saturn", "vehicle_journeys.xml", "3", None),
        ("Saturn", "vehicle_journeys.xml", "1", "Earth"),
    ],
)
def test_data_match_origin_ref_errors(
    mvj_origin_ref, filename, sequence_number, txc_stop_point
):
    mvj = MonitoredVehicleJourney(
        origin_ref=mvj_origin_ref, operator_ref="Itoworld", vehicle_ref="Bertha"
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename=filename, sequence_number=sequence_number
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_origin_ref(mvj, txc_vehicle_journey, result)

    assert result.sirivm_value(SirivmField.ORIGIN_REF) == mvj_origin_ref
    assert result.txc_value(SirivmField.ORIGIN_REF) == txc_stop_point
    assert not result.matches(SirivmField.ORIGIN_REF)
    assert len(result.errors.get(ErrorCategory.ORIGIN_REF)) > 0


@pytest.mark.parametrize(
    "mvj_destination_name,filename,sequence_number",
    [
        ("Pluto", "vehicle_journeys.xml", "1"),
        ("Mercury", "vehicle_journeys.xml", "2"),
    ],
)
def test_data_match_destination_name_succeeds(
    mvj_destination_name, filename, sequence_number
):
    mvj = MonitoredVehicleJourney(
        destination_name=mvj_destination_name,
        operator_ref="Itoworld",
        vehicle_ref="Bertha",
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename=filename, sequence_number=sequence_number
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_destination_name(mvj, txc_vehicle_journey, result)

    assert result.sirivm_value(SirivmField.DESTINATION_NAME) == mvj_destination_name
    assert result.txc_value(SirivmField.DESTINATION_NAME) == mvj_destination_name
    assert result.matches(SirivmField.DESTINATION_NAME)
    assert len(result.errors.get(ErrorCategory.DESTINATION_NAME)) == 0


@pytest.mark.parametrize(
    "mvj_destination_name,filename,sequence_number,txc_destination_display",
    [
        (None, "vehicle_journeys.xml", "1", None),
        ("Mercury", "vehicle_journeys.xml", "1", "Pluto"),
        ("Pluto", "vehicle_journeys.xml", "2", "Mercury"),
        ("Mercury", "vehicle_journeys.xml", "3", None),
    ],
)
def test_data_match_destination_name_errors(
    mvj_destination_name, filename, sequence_number, txc_destination_display
):
    mvj = MonitoredVehicleJourney(
        destination_name=mvj_destination_name,
        operator_ref="Itoworld",
        vehicle_ref="Bertha",
    )
    txc_vehicle_journey = get_txc_vehicle_journey(
        filename=filename, sequence_number=sequence_number
    )
    data_matching = DataMatching()
    result = ValidationResult()
    data_matching.data_match_destination_name(mvj, txc_vehicle_journey, result)

    assert result.sirivm_value(SirivmField.DESTINATION_NAME) == mvj_destination_name
    assert result.txc_value(SirivmField.DESTINATION_NAME) == txc_destination_display
    assert not result.matches(SirivmField.DESTINATION_NAME)
    assert len(result.errors.get(ErrorCategory.DESTINATION_NAME)) > 0
