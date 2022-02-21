import pytest

from transit_odp.data_quality.pti.factories import SchemaFactory
from transit_odp.data_quality.pti.models import Schema
from transit_odp.data_quality.pti.tests.conftest import JSONFile, TXCFile
from transit_odp.data_quality.pti.validators import PTIValidator
from transit_odp.timetables.pti import PTI_PATH

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(("has_location", "expected"), [(True, True), (False, False)])
def test_journey_pattern_location(has_location, expected):
    location = """
    <Location>
        <Easting>442914</Easting>
        <Northing>295186</Northing>
    </Location>
    """

    journey_pattern = """
    <JourneyPattern id="JP1">
        <Direction>outbound</Direction>
        <LayoverPoint id="lay_1">
            <Duration>PT16M</Duration>
            <Name>Side Road</Name>
            {0}
            <MinimumDuration>PT10M</MinimumDuration>
        </LayoverPoint>
        <RouteRef>R1</RouteRef>
    </JourneyPattern>
    """

    if has_location:
        xml = journey_pattern.format(location)
    else:
        xml = journey_pattern.format("")

    OBSERVATION_ID = 19
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("interchange_activity", "guaranteed_connection", "change_line_number", "expected"),
    [
        ("through", "true", "true", True),
        ("", "true", "true", False),
        ("through", "", "true", False),
        ("through", "true", "", False),
    ],
)
def test_vehicle_journey_interchange(
    interchange_activity, guaranteed_connection, change_line_number, expected
):
    vehicle_journey = """
    <VehicleJourney>
        <VehicleJourneyCode>VJ_3</VehicleJourneyCode>
        <ServiceRef>SV_1</ServiceRef>
        <LineRef>Ln_1</LineRef>
        <VehicleJourneyRef>VJ_1</VehicleJourneyRef>
        <VehicleJourneyInterchange>
            <MinInterchangeTime>PT0M</MinInterchangeTime>
            {0}
            {1}
            {2}
            <InboundVehicleJourneyRef>VJ1-MF-OB-1</InboundVehicleJourneyRef>
            <InboundStopPointRef>269039050</InboundStopPointRef>
            <OutboundVehicleJourneyRef>VJ17-MF-IB-2</OutboundVehicleJourneyRef>
            <OutboundStopPointRef>269039050</OutboundStopPointRef>
        </VehicleJourneyInterchange>
        <DepartureTime>12:02:00</DepartureTime>
    </VehicleJourney>
    """

    if interchange_activity:
        interchange_activity = "<InterchangeActivity>{0}</InterchangeActivity>".format(
            interchange_activity
        )
    if guaranteed_connection:
        guaranteed_connection = (
            "<GuaranteedConnection>{0}</GuaranteedConnection>".format(
                guaranteed_connection
            )
        )

    if change_line_number:
        change_line_number = "<ChangeLineNumber>{0}</ChangeLineNumber>".format(
            change_line_number
        )

    xml = vehicle_journey.format(
        interchange_activity, guaranteed_connection, change_line_number
    )

    OBSERVATION_ID = 50
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("interchange_activity", "guaranteed_connection", "change_line_number", "expected"),
    [
        ("through", "true", "true", True),
        ("", "true", "true", False),
        ("through", "", "true", False),
        ("through", "true", "", False),
    ],
)
def test_journey_pattern_interchange(
    interchange_activity, guaranteed_connection, change_line_number, expected
):
    service = """
    <Service>
        <JourneyPatternInterchange>
            <MinInterchangeTime>PT0M</MinInterchangeTime>
            {0}
            {1}
            {2}
            <Inbound>
                <JourneyPatternRef>JP_12-16-_-y08-1-1-H-1</JourneyPatternRef>
                <StopUsageRef>269039050</StopUsageRef>
            </Inbound>
            <Outbound>
                <JourneyPatternRef>JP_12-16-_-y08-1-5-R-2</JourneyPatternRef>
                <StopUsageRef>269039050</StopUsageRef>
            </Outbound>
        </JourneyPatternInterchange>
    </Service>
    """

    if interchange_activity:
        interchange_activity = "<InterchangeActivity>{0}</InterchangeActivity>".format(
            interchange_activity
        )
    if guaranteed_connection:
        guaranteed_connection = (
            "<GuaranteedConnection>{0}</GuaranteedConnection>".format(
                guaranteed_connection
            )
        )

    if change_line_number:
        change_line_number = "<ChangeLineNumber>{0}</ChangeLineNumber>".format(
            change_line_number
        )

    xml = service.format(
        interchange_activity, guaranteed_connection, change_line_number
    )

    OBSERVATION_ID = 52
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("elements", "id_", "expected"),
    [
        (("NationalOperatorCode", "LicenceNumber"), 104, True),
        (tuple(), 104, False),
        (("NationalOperatorCode",), 104, True),
        (("LicenceNumber",), 104, False),
        (("NationalOperatorCode", "LicenceNumber"), 127, True),
        (tuple(), 127, False),
        (("NationalOperatorCode",), 127, False),
        (("LicenceNumber",), 127, True),
    ],
)
def test_operator_elements(elements, id_, expected):
    operators = """
    <Operators>
        <Operator>
            {0}
        </Operator>
    </Operators>
    """
    children = "\n".join("<{0}>ABC123</{0}>".format(e) for e in elements)
    xml = operators.format(children)

    OBSERVATION_ID = id_
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("elements", "id_", "expected"),
    [
        (("PublicUse",), 105, True),
        (tuple(), 105, False),
        (("Blah",), 105, False),
    ],
)
def test_service_elements(elements, id_, expected):
    operators = """
    <Services>
        <Service>
            {0}
        </Service>
    </Services>
    """
    children = "\n".join("<{0}>true</{0}>".format(e) for e in elements)
    xml = operators.format(children)

    OBSERVATION_ID = id_
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("elements", "id_", "expected"),
    [
        (("OperatorRef",), 110, True),
        (("Direction",), 111, True),
        (("RouteRef",), 112, True),
        (("JourneyPatternSectionRefs",), 113, True),
        (("JourneyPatternSectionRefs",), 112, False),
        (("JourneyPatternSectionRefs",), 111, False),
        (("OperatorRef", "JourneyPatternSectionRefs", "RouteRef"), 110, True),
        (("JourneyPatternSectionRefs", "RouteRef", "Direction"), 111, True),
        (("JourneyPatternSectionRefs", "RouteRef", "Direction"), 112, True),
        (("JourneyPatternSectionRefs", "RouteRef", "Direction"), 113, True),
        (("JourneyPatternSectionRefs", "RouteRef"), 111, False),
        (tuple(), 110, False),
        (tuple(), 111, False),
        (tuple(), 112, False),
        (tuple(), 113, False),
    ],
)
def test_journey_pattern_elements(elements, id_, expected):
    operators = """
    <StandardService>
        <JourneyPattern id="JP1">
            {0}
        </JourneyPattern>
    </StandardService>
    """
    children = "\n".join("<{0}>doesntmatter</{0}>".format(e) for e in elements)
    xml = operators.format(children)

    OBSERVATION_ID = id_
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("elements", "id_", "expected"),
    [
        (("RouteLinkRef",), 114, True),
        (tuple(), 114, False),
    ],
)
def test_journey_pattern_timing_link_elements(elements, id_, expected):
    operators = """
    <JourneyPatternSection>
        <JourneyPatternTimingLink id="JPTL1">
            {0}
        </JourneyPatternTimingLink>
    </JourneyPatternSection>
    """
    children = "\n".join("<{0}>doesntmatter</{0}>".format(e) for e in elements)
    xml = operators.format(children)

    OBSERVATION_ID = id_
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("has_from", "has_to", "id_", "expected"),
    [
        (True, True, 129, True),
        (True, True, 131, True),
        (False, True, 129, False),
        (True, False, 131, False),
    ],
)
def test_timing_status(has_from, has_to, id_, expected):
    operators = """
    <JourneyPatternSection>
        <JourneyPatternTimingLink id="JPTL1">
            <From>
                {0}
                <DynamicDestinationDisplay>Hospital</DynamicDestinationDisplay>
            </From>
            <To>
                {1}
                <DynamicDestinationDisplay>Hospital Car Park</DynamicDestinationDisplay>
            </To>
        </JourneyPatternTimingLink>
    </JourneyPatternSection>
    """

    from_ = ""
    if has_from:
        from_ = "<TimingStatus>PTP</TimingStatus>"

    to_ = ""
    if has_to:
        to_ = "<TimingStatus>PTP</TimingStatus>"

    xml = operators.format(from_, to_)

    OBSERVATION_ID = id_
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("has_operator_ref", "expected"),
    [(True, True), (False, False)],
)
def test_vehicle_journey_operator_ref(has_operator_ref, expected):
    vehicle_journeys = """
    <VehicleJourneys>
        <VehicleJourney>
            {0}
            <VehicleJourneyCode>vj_1</VehicleJourneyCode>
            <ServiceRef>FIN50</ServiceRef>
            <LineRef>l_1</LineRef>
            <JourneyPatternRef>jp_1</JourneyPatternRef>
            <DepartureTime>07:00:00</DepartureTime>
        </VehicleJourney>
    </VehicleJourneys>
    """

    operator_ref = ""
    if has_operator_ref:
        operator_ref = "<OperatorRef>O1</OperatorRef>"

    xml = vehicle_journeys.format(operator_ref)
    OBSERVATION_ID = 117
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("has_run_time", "expected"),
    [(True, True), (False, False)],
)
def test_vehicle_journey_timing_link_run_time(has_run_time, expected):
    vehicle_journeys = """
    <VehicleJourneys>
        <VehicleJourney>
            <VehicleJourneyCode>vj_1</VehicleJourneyCode>
            <ServiceRef>FIN50</ServiceRef>
            <LineRef>l_1</LineRef>
            <JourneyPatternRef>jp_1</JourneyPatternRef>
            <DepartureTime>07:00:00</DepartureTime>
            <VehicleJourneyTimingLink id="VJTL5">
                <JourneyPatternTimingLinkRef>JPTL5</JourneyPatternTimingLinkRef>
                {0}
                <From>
                    <Activity>pickUp</Activity>
                </From>
            </VehicleJourneyTimingLink>
        </VehicleJourney>
    </VehicleJourneys>
    """

    run_time = ""
    if has_run_time:
        run_time = "<RunTime>PT20M</RunTime>"

    xml = vehicle_journeys.format(run_time)
    OBSERVATION_ID = 118
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)

    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected
