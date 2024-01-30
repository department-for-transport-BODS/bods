from datetime import timedelta
from pathlib import Path

import pytest
from dateutil import parser

from transit_odp.data_quality.pti.factories import SchemaFactory
from transit_odp.data_quality.pti.models import Schema
from transit_odp.data_quality.pti.tests.conftest import JSONFile, TXCFile
from transit_odp.data_quality.pti.validators import PTIValidator
from transit_odp.naptan.factories import StopPointFactory
from transit_odp.timetables.pti import PTI_PATH

DATA_DIR = Path(__file__).parent / "data"
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("no_of_services,expected", [(2, False), (0, False)])
def test_start_date_provisional_invalid(no_of_services, expected):
    service = """
    <Service>
        <ServiceCode>{}</ServiceCode>
        <Lines>
            <Line id="L1">
                <LineName>1A</LineName>
            </Line>
            <Line id="L2">
                <LineName>1B</LineName>
            </Line>
        </Lines>
        <OperatingPeriod>
            <StartDate>2004-01-01</StartDate>
            <EndDate>2005-06-13</EndDate>
        </OperatingPeriod>
    </Service>
    """
    services = "\n".join(
        [service.format(service_code) for service_code in range(no_of_services)]
    )
    xml = "<Services>{}</Services>".format(services)

    OBSERVATION_ID = 17
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize("no_of_services,expected", [(1, True)])
def test_start_date_provisional_valid(no_of_services, expected):
    service = """
    <Service>
        <ServiceCode>{}</ServiceCode>
        <Lines>
            <Line id="L1">
                <LineName>1A</LineName>
            </Line>
            <Line id="L2">
                <LineName>1B</LineName>
            </Line>
        </Lines>
        <OperatingPeriod>
            <StartDate>2004-01-01</StartDate>
            <EndDate>2005-06-13</EndDate>
        </OperatingPeriod>
        <StandardService>
            <Origin>Putteridge High School</Origin>
        </StandardService>
    </Service>
    """
    service_code = "PB0002032:467"
    services = "\n".join([service.format(service_code)])
    xml = "<Services>{}</Services>".format(services)

    OBSERVATION_ID = 17
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("journey_ids", "expected"),
    [
        (["JP1", "JP2"], True),
        (["JP2"], True),
        ([], False),
    ],
)
def test_service_has_journey_pattern(journey_ids, expected):
    pattern = """
    <JourneyPattern id="{0}">
        <Direction>outbound</Direction>
        <RouteRef>R2</RouteRef>
        <JourneyPatternSectionRefs>JPS1</JourneyPatternSectionRefs>
        <JourneyPatternSectionRefs>JPS3</JourneyPatternSectionRefs>
    </JourneyPattern>
    """

    pattern = "\n".join(pattern.format(id_) for id_ in journey_ids)
    service = """
    <Services>
        <Service>
            <ServiceCode>1</ServiceCode>
        </Service>
        <StandardService>
            <Origin>Bus Station</Origin>
            <Destination>Exchange</Destination>
            <Vias>
                <Via>School</Via>
            </Vias>
            <UseAllStopPoints>false</UseAllStopPoints>
            {0}
        </StandardService>
    </Services>
    """
    xml = service.format(pattern)

    OBSERVATION_ID = 21
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


def test_line_outbound_description_true():
    lines = """
    <Lines>
        <Line id="L1">
            <LineName>1</LineName>
            <OutboundDescription>
                <Origin>sdjfkjsdf</Origin>
                <Destination>sdfjsjdfh</Destination>
                <Description>A description</Description>
            </OutboundDescription>
        </Line>
    </Lines>
    """
    xml = lines
    OBSERVATION_ID = 25
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid


def test_line_inbound_description_true():
    lines = """
    <Lines>
        <Line id="L1">
            <LineName>1</LineName>
            <InboundDescription>
                <Origin>sdjfkjsdf</Origin>
                <Destination>sdfjsjdfh</Destination>
                <Description>A description</Description>
            </InboundDescription>
        </Line>
    </Lines>
    """
    xml = lines
    OBSERVATION_ID = 25
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid


def test_line_description_false():
    lines = """
    <Lines>
        <Line id="L1">
            <LineName>1</LineName>
        </Line>
    </Lines>
    """
    xml = lines
    OBSERVATION_ID = 25
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert not is_valid


@pytest.mark.parametrize(
    ("service_code", "expected"),
    [
        ("S1", False),
        ("PF0000459:134", True),
        ("PF0000459:", False),
        ("PF0000459:ABC", True),
        ("PD1073423:4", True),
        ("UZ000WNCT:GTT32", True),
        ("PD0001111:6:7", False),
    ],
)
def test_service_code_format(service_code, expected):
    services = """
    <Services>
        <Service>
            <ServiceCode>{0}</ServiceCode>
        </Service>
    </Services>
    """
    xml = services.format(service_code)
    OBSERVATION_ID = 18
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("start_date", "end_date_in_days", "expected"),
    [
        ("2005-01-01", None, True),
        ("2005-01-01", 0, True),
        ("2005-01-01", 1, True),
        ("2005-01-01", 365, True),
        ("2005-01-01", 366, True),
        ("2005-01-01", 4026, True),
        ("2005-01-01", 4027, False),
        ("2005-01-01", 8000, False),
        ("2005-01-01", -1, False),
    ],
)
def test_operating_period_end_date(start_date, end_date_in_days, expected):
    operating_period = """
    <Service>
        <ServiceCode>025</ServiceCode>
        <Lines>
            <Line id="2">
                <LineName>215</LineName>
            </Line>
            <Line id="90">
                <LineName>215A</LineName>
            </Line>
        </Lines>
        <OperatingPeriod>
            {0}
            {1}
        </OperatingPeriod>
    </Service>
    """

    if end_date_in_days is not None:
        end_date = parser.parse(start_date) + timedelta(days=end_date_in_days)
        end_date = f"<EndDate>{end_date:%Y-%m-%d}</EndDate>"
    else:
        end_date = ""

    start_date = f"<StartDate>{start_date}</StartDate>"

    xml = operating_period.format(start_date, end_date)
    OBSERVATION_ID = 20
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("bodp3613lineidfail.xml", False),
        ("bodp3613lineidfailspaces.xml", False),
        ("bodp3613lineidpass.xml", True),
    ],
)
def test_line_id_format(filename, expected):
    OBSERVATION_ID = 24
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
    ("service", "expected"),
    [("FlexibleService", True), ("StandardService", True), ("", False)],
)
def test_flexible_service(service, expected):
    service_template = """
    <Service>
        <ServiceCode>FIN50</ServiceCode>
        <Lines>
            <Line id="l_1">
                <LineName>A1</LineName>
            </Line>
        </Lines>
        {0}
    </Service>
    """

    if service:
        if service == "FlexibleService":
            service = "<ServiceClassification><Flexible/></ServiceClassification><{0}></{0}>".format(
                service
            )
        else:
            service = "<{0}></{0}>".format(service)

    service = service_template.format(service)
    xml = "<Services>{0}</Services>".format(service)

    OBSERVATION_ID = 22
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


def test_validate_less_than_two_lines():
    service = """
    <Service>
        <ServiceCode>FIN50</ServiceCode>
        <Lines>
            <Line id="l_1">
                <LineName>A1</LineName>
            </Line>
        </Lines>
    </Service>
    """
    xml = "<Services>{0}</Services>".format(service)

    OBSERVATION_ID = 23
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
        ("nonrelatedlines.xml", False),
        ("relatedlinesbylocalityname.xml", True),
        ("relatedlinesbyjp.xml", True),
        ("relatedlinesbystops.xml", True),
    ],
)
def test_related_lines(filename, expected):
    OBSERVATION_ID = 23
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc_path = DATA_DIR / filename
    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid == expected


def test_non_related_with_stop_areas():
    # The following atco codes come from nonrelatedlines.xml one stop in each line
    l1stop = 9990000001
    l1Nstop = 9990000026
    stop_areas_in_common = ["match"]
    StopPointFactory(atco_code=l1stop, stop_areas=stop_areas_in_common)
    StopPointFactory(atco_code=l1Nstop, stop_areas=stop_areas_in_common)
    StopPointFactory.create_batch(3, stop_areas=[])

    OBSERVATION_ID = 23
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc_path = DATA_DIR / "nonrelatedlines.xml"
    with txc_path.open("r") as txc:
        assert pti.is_valid(txc)
