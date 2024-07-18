import random
from pathlib import Path

import pytest

from transit_odp.data_quality.pti.constants import BANK_HOLIDAYS, SCOTTISH_BANK_HOLIDAYS
from transit_odp.data_quality.pti.factories import SchemaFactory
from transit_odp.data_quality.pti.models import Schema
from transit_odp.data_quality.pti.tests.conftest import JSONFile, TXCFile
from transit_odp.data_quality.pti.validators import PTIValidator
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.otc.constants import API_TYPE_WECA
from transit_odp.otc.factories import (
    LocalAuthorityFactory,
    ServiceModelFactory,
    UILtaFactory,
)
from transit_odp.timetables.pti import PTI_PATH

DATA_DIR = Path(__file__).parent / "data"
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("days", "expected"),
    [
        (["Monday", "Tuesday"], True),
        (["Tuesday"], True),
        (["Wednesday"], True),
        (["Thursday"], True),
        (["Friday"], True),
        (["Saturday"], True),
        (["Sunday"], True),
        (["MondayToFriday"], False),
    ],
)
def test_days_of_week(days, expected):
    operating_period = """
    <OperatingProfile>
        <RegularDayType>
            <DaysOfWeek>
                {}
            </DaysOfWeek>
        </RegularDayType>
    </OperatingProfile>
    """
    days_of_week = "\n".join(f"<{day}/>" for day in days)
    xml = operating_period.format(days_of_week)

    OBSERVATION_ID = 41
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("shift", "expected"),
    [
        ("1", True),
        ("", True),
        ("+1", False),
        ("+2", False),
        ("-1", False),
        ("-2", False),
    ],
)
def test_departure_day_shift(shift, expected):
    if shift:
        day_shift = "<DepartureDayShift>{0}</DepartureDayShift>".format(shift)
    else:
        day_shift = ""

    journey = """
    <VehicleJourney>
        <OperatingProfile>
            <RegularDayType>
                <DaysOfWeek>
                    <MondayToFriday/>
                </DaysOfWeek>
            </RegularDayType>
        </OperatingProfile>
        <VehicleJourneyCode>VJ_A</VehicleJourneyCode>
        <ServiceRef>S1</ServiceRef>
        <LineRef>L1N</LineRef>
        <JourneyPatternRef>JP1</JourneyPatternRef>
        <DepartureTime>23:55:00</DepartureTime>
        {0}
    </VehicleJourney>
    """
    xml = journey.format(day_shift)
    OBSERVATION_ID = 46
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


def test_bank_holidays_days_of_operation_true():
    day_type = """
    <DayType id="day_04">
        <Name>Bank Holiday Service</Name>
        <RegularDayType>
            <HolidaysOnly/>
        </RegularDayType>
        <BankHolidayOperation>
        <DaysOfOperation>
        {0}
        </DaysOfOperation>
        </BankHolidayOperation>
    </DayType>
    """

    days_of_operation = "\n".join("<{0}/>".format(d) for d in BANK_HOLIDAYS)
    xml = day_type.format(days_of_operation)

    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid


def test_bank_holidays_days_of_operation_with_comments_true():
    day_type = """
    <DayType id="day_04">
        <Name>Bank Holiday Service</Name>
        <RegularDayType>
            <HolidaysOnly/>
        </RegularDayType>
        <BankHolidayOperation>
        <DaysOfOperation>
        <!-- Comment -->
        {0}
        </DaysOfOperation>
        </BankHolidayOperation>
    </DayType>
    """

    days_of_operation = "\n".join("<{0}/>".format(d) for d in BANK_HOLIDAYS)
    xml = day_type.format(days_of_operation)

    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid


def test_bank_holidays_missing_days_false():
    day_type = """
    <DayType id="day_04">
        <Name>Bank Holiday Service</Name>
        <RegularDayType>
            <HolidaysOnly/>
        </RegularDayType>
        <BankHolidayOperation>
        <DaysOfOperation>
        {0}
        </DaysOfOperation>
        </BankHolidayOperation>
    </DayType>
    """
    days_of_operation = "\n".join("<{0}/>".format(d) for d in BANK_HOLIDAYS[:6])
    xml = day_type.format(days_of_operation)

    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert not is_valid


def test_bank_holidays_split_true():
    day_type = """
    <DayType id="day_04">
        <Name>Bank Holiday Service</Name>
        <RegularDayType>
            <HolidaysOnly/>
        </RegularDayType>
        <BankHolidayOperation>
        <DaysOfOperation>
        {0}
        </DaysOfOperation>
        <DaysOfNonOperation>
        {1}
        </DaysOfNonOperation>
        </BankHolidayOperation>
    </DayType>
    """
    days = list(BANK_HOLIDAYS)
    random.shuffle(days)

    mid_point = len(days) // 2
    operation = days[:mid_point]
    non_operation = days[mid_point:]

    days_of_operation = "\n".join("<{0}/>".format(d) for d in operation)
    days_of_non_operation = "\n".join("<{0}/>".format(d) for d in non_operation)

    xml = day_type.format(days_of_operation, days_of_non_operation)

    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid


def test_bank_holidays_split_missing_days_false():
    day_type = """
    <DayType id="day_04">
        <Name>Bank Holiday Service</Name>
        <RegularDayType>
            <HolidaysOnly/>
        </RegularDayType>
        <BankHolidayOperation>
        <DaysOfOperation>
        {0}
        </DaysOfOperation>
        <DaysOfNonOperation>
        {1}
        </DaysOfNonOperation>
        </BankHolidayOperation>
    </DayType>
    """
    days = list(BANK_HOLIDAYS)
    operation = days[:1]
    non_operation = days[1:2]

    days_of_operation = "\n".join("<{0}/>".format(d) for d in operation)
    days_of_non_operation = "\n".join("<{0}/>".format(d) for d in non_operation)

    xml = day_type.format(days_of_operation, days_of_non_operation)

    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert not is_valid


def test_bank_holidays_split_duplicates_false():
    day_type = """
    <DayType id="day_04">
        <Name>Bank Holiday Service</Name>
        <RegularDayType>
            <HolidaysOnly/>
        </RegularDayType>
        <BankHolidayOperation>
        <DaysOfOperation>
        {0}
        </DaysOfOperation>
        <DaysOfNonOperation>
        {1}
        </DaysOfNonOperation>
        </BankHolidayOperation>
    </DayType>
    """
    days = list(BANK_HOLIDAYS)
    random.shuffle(days)

    days_of_operation = "\n".join("<{0}/>".format(d) for d in days)
    days_of_non_operation = "\n".join("<{0}/>".format(d) for d in days)

    xml = day_type.format(days_of_operation, days_of_non_operation)

    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert not is_valid


def test_bank_holidays_scottish_holidays_true():
    day_type = """
    <DayType id="day_04">
        <Name>Bank Holiday Service</Name>
        <RegularDayType>
            <HolidaysOnly/>
        </RegularDayType>
        <BankHolidayOperation>
        <DaysOfOperation>
        {0}
        </DaysOfOperation>
        </BankHolidayOperation>
    </DayType>
    """

    days_of_operation = "\n".join(
        "<{0}/>".format(d) for d in BANK_HOLIDAYS + SCOTTISH_BANK_HOLIDAYS
    )
    xml = day_type.format(days_of_operation)

    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid


def test_other_public_holidays_true():
    day_type = """
    <DayType id="day_04">
        <Name>Bank Holiday Service</Name>
        <RegularDayType>
            <HolidaysOnly/>
        </RegularDayType>
        <BankHolidayOperation>
        <DaysOfOperation>
            {0}
            <OtherPublicHoliday>
              <Description>April Fools' Day</Description>
              <Date>2022-04-01</Date>
            </OtherPublicHoliday>
            <OtherPublicHoliday>
              <Description>Star Wars Day</Description>
              <Date>2022-05-04</Date>
            </OtherPublicHoliday>
        </DaysOfOperation>
        <DaysOfNonOperation>
            {1}
            <OtherPublicHoliday>
              <Description>Platinum Jubilee</Description>
              <Date>2022-06-03</Date>
            </OtherPublicHoliday>
        </DaysOfNonOperation>
        </BankHolidayOperation>
    </DayType>
    """
    days_of_operation = "\n".join("<{0}/>".format(d) for d in BANK_HOLIDAYS[:1])
    days_of_non_operation = "\n".join("<{0}/>".format(d) for d in BANK_HOLIDAYS[1:])

    xml = day_type.format(days_of_operation, days_of_non_operation)

    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("destinationdisplayjourneypattern.xml", True),
        ("dynamicdisplaytiminglinks.xml", True),
        ("dynamicdisplaytiminglinksfail.xml", False),
    ],
)
def test_destination_display(filename, expected):
    OBSERVATION_ID = 47
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("has_vj_ref", "has_profile", "expected"),
    [
        (True, False, True),
        (False, False, True),
        (False, True, True),
        (True, True, False),
    ],
)
def test_validate_vehicle_journey_ref(has_vj_ref, has_profile, expected):
    vehicle_journey = """
    <VehicleJourneys>
        <VehicleJourney>
            {0}
            <LineRef>L1</LineRef>
            <ServiceRef>S1</ServiceRef>
            <GarageRef>1</GarageRef>
            {1}
        </VehicleJourney>
    </VehicleJourneys>
    """

    vj_ref = ""
    if has_vj_ref:
        vj_ref = "<VehicleJourneyRef>VJ1</VehicleJourneyRef>"

    profile = ""
    if has_profile:
        profile = """
        <OperatingProfile>
            <RegularDayType>
                <DaysOfWeek>
                    <MondayToFriday/>
                </DaysOfWeek>
            </RegularDayType>
        </OperatingProfile>
        """

    xml = vehicle_journey.format(vj_ref, profile)
    OBSERVATION_ID = 39
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


def test_bank_holidays_scottish_holidays_with_service_ref():
    services = ServiceModelFactory(
        registration_number="PK0003556/55", service_number="100|200|Bellford"
    )
    ui_lta = UILtaFactory(name="Dorset County Council")
    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=[services],
    )
    AdminAreaFactory(traveline_region_id="S", ui_lta=ui_lta)

    filename = "pti/scotish_holidays.xml"
    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid


def test_bank_holidays_scottish_holidays_with_service_ref_WECA():
    services = ServiceModelFactory(
        registration_number="PK0003556/55",
        service_number="100|200|Bellford",
        atco_code="010",
        api_type=API_TYPE_WECA,
    )
    ui_lta = UILtaFactory(name="Dorset County Council")
    AdminAreaFactory(traveline_region_id="S", ui_lta=ui_lta, atco_code="010")

    filename = "pti/scotish_holidays.xml"
    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid


def test_bank_holidays_english_holidays_with_service_ref():
    services = ServiceModelFactory(
        registration_number="PK0003556/55", service_number="100|200|Bellford"
    )
    ui_lta = UILtaFactory(name="Dorset County Council")
    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=[services],
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    filename = "pti/english_holidays.xml"
    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid


def test_bank_holidays_english_holidays_with_service_ref_WECA():
    services = ServiceModelFactory(
        registration_number="PK0003556/55",
        service_number="100|200|Bellford",
        atco_code="010",
        api_type=API_TYPE_WECA,
    )
    ui_lta = UILtaFactory(name="Dorset County Council")
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code="010")

    filename = "pti/english_holidays.xml"
    OBSERVATION_ID = 43
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc_path = DATA_DIR / filename

    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid
