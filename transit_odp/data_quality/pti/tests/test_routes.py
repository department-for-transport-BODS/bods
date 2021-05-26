import pytest

from transit_odp.data_quality.pti.factories import SchemaFactory
from transit_odp.data_quality.pti.models import Schema
from transit_odp.data_quality.pti.tests.conftest import JSONFile, TXCFile
from transit_odp.data_quality.pti.validators import PTIValidator
from transit_odp.timetables.utils import PTI_PATH


@pytest.mark.parametrize(
    ("manoeuvre", "expected"),
    [("<ReversingManoeuvres>fast</ReversingManoeuvres>", False), ("", True)],
)
def test_route_contains_reversing_manoeuvres(manoeuvre, expected):
    routes = """
    <Routes>
        <Route id="R1">
            <Description xml:lang="en">Hospital</Description>
            <RouteSectionRef>RS1</RouteSectionRef>
            {0}
        </Route>
    </Routes>
    """
    xml = routes.format(manoeuvre)

    OBSERVATION_ID = 30
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("location_count", "expected"), [(1, False), (2, True), (0, True)]
)
def test_track_has_at_least_two_locations_true(location_count, expected):
    location = """
    <Location>
        <Easting>44291{}</Easting>
        <Northing>295186</Northing>
    </Location>
    """
    track = """
    <Track>
        <Mapping>
        {0}
        </Mapping>
    </Track>
    """
    journey = """
    <PositioningLink>
        <RunTime>PT20M</RunTime>
        <From>
            <GarageRef>GW1</GarageRef>
        </From>
        <DutyCrewRef>234</DutyCrewRef>
        {0}
    </PositioningLink>
    """

    locations = "\n".join(location.format(i) for i in range(location_count))
    track = track.format(locations) if locations else ""
    xml = journey.format(track)

    OBSERVATION_ID = 32
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("from_stop_ref", "to_stop_ref", "expected"),
    [("123", "124", True), ("123", "122", True), ("122", "123", False)],
)
def test_unique_route_links(from_stop_ref, to_stop_ref, expected):
    routes = """
    <RouteSections>
        <RouteSection id="rs_1">
            <RouteLink id="rl_1">
                <From>
                    <StopPointRef>122</StopPointRef>
                </From>
                <To>
                    <StopPointRef>123</StopPointRef>
                </To>
                <Distance>5573</Distance>
                <Direction>outbound</Direction>
            </RouteLink>
            <RouteLink id="rl_2">
                <From>
                    <StopPointRef>{0}</StopPointRef>
                </From>
                <To>
                    <StopPointRef>{1}</StopPointRef>
                </To>
                <Distance>4512</Distance>
                <Direction>outbound</Direction>
            </RouteLink>
        </RouteSection>
    </RouteSections>
    """

    xml = routes.format(from_stop_ref, to_stop_ref)
    OBSERVATION_ID = 29
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("has_direction", "expected"),
    [(True, False), (False, True)],
)
def test_route_link_direction(has_direction, expected):
    direction = "<Direction>outbound</Direction>"
    route_sections = """
    <RouteSections>
        <RouteSection id="rs_1">
            <RouteLink id="rl_1">
                <Distance>5573</Distance>
                {0}
            </RouteLink>
        </RouteSection>
    </RouteSections>
    """

    if has_direction:
        xml = route_sections.format(direction)
    else:
        xml = route_sections.format("")

    OBSERVATION_ID = 31
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected
