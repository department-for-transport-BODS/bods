from dataclasses import dataclass
from enum import Enum, unique
from typing import Dict, Final, Optional

from transit_odp.data_quality import models
from transit_odp.data_quality.models.warnings import (
    LineExpiredWarning,
    LineMissingBlockIDWarning,
)

_ANCHOR: Final = '<a class="govuk-link" target="_blank" href="{0}">{0}</a>'
_TRAVEL_LINE_ANCHOR = _ANCHOR.format(
    "https://www.travelinedata.org.uk/traveline-open-data/"
    "transport-operations/browse/"
)
_TRANSXCHANGE_ANCHOR: Final = _ANCHOR.format(
    "https://www.gov.uk/government/collections/transxchange"
)
_LINE_BREAK = "<br/><br/>"


@unique
class Level(Enum):
    critical = "Critical"
    advisory = "Advisory"


@unique
class Category(Enum):
    stops = "Stops"
    timing = "Timing"
    journey = "Journey"
    data_set = "Data set"


class CheckBasis(Enum):
    stops = "stops"
    lines = "lines"
    timing_patterns = "timing_patterns"
    vehicle_journeys = "vehicle_journeys"
    data_set = "data_set"


@dataclass
class Observation:
    level: Level
    category: Category
    title: str
    text: str
    list_url_name: str
    model: Optional[models.DataQualityWarningBase]
    extra_info: Optional[Dict[str, str]] = None
    impacts: str = None
    weighting: float = None
    check_basis: CheckBasis = None
    resolve: str = None

    @property
    def type(self):
        return self.category.value

# TODO: DQSMIGRATION: Move to dqs module
IncorrectNocObservation = Observation(
    title="Incorrect NOC code",
    text="",
    impacts=(
        "This observation identifies where the National Operator Code (NOC) used in the data is not registered to the your Organisation profile."
        + _LINE_BREAK
        + "NOCs are used by data consumers to know which operator is running the service, and to match the data with bus location and fares data. This ability improves the quality of information available to passengers."
    ),
    resolve=(
        "Please check the NOC(s) on your data is correct for your organisation and is assigned to your Organisation profile."
        + _LINE_BREAK
        + "Operators can find their organisation’s NOC by browsing the Traveline NOC database here:"
        + _LINE_BREAK
        + _TRAVEL_LINE_ANCHOR
        + _LINE_BREAK
        + "Operators can assign a NOC to their account by going to My account (in the top right-hand side of the dashboard) and choosing Organisation profile."
    ),
    model=models.IncorrectNOCWarning,
    list_url_name="dq:incorrect-noc-list",
    level=Level.critical,
    category=Category.data_set,
    weighting=0.12,
    check_basis=CheckBasis.data_set,
)
MissingBlockNumber = Observation(
    title="Missing block number",
    text=(
        "This observation highlights missing valid block numbers for services "
        "which are beginning in 7 days time. "
        "The block number needs to be the same as the "
        "corresponding object in the bus location data field ‘BlockRef’. "
        "</br></br>"
        "Block number is also known as bus workings number, most frequently "
        "populated using running board information. "
        "It’s a unique identifier or code (usually a simple number) that "
        "is used for all the journeys an individual bus is scheduled to work. "
        "</br></br>"
        "If an operator does not have a documented running board, they can "
        "create one by allocating each of their vehicles a ‘code’. "
        "For each of the journeys operated by the same vehicle, the journey "
        "should be given a consistent identifier as the input for "
        "both the TransXChange (Block number) and SIRI-VM (Block ref). "
        "For example, Vehicle 1, could have block number = 1 allocated to all "
        "the journeys that will be completed by vehicle 1."
    ),
    impacts=(
        "This is a key piece of information for consumers to use in order to match "
        "across different data types. "
        "This enables consumers to improve their journey predictions for passengers "
        "by considering cross journey predictions. "
        "Meaning if a vehicle is late on a journey, the next journey is likely to "
        "also be running late."
    ),
    model=LineMissingBlockIDWarning,
    list_url_name="dq:line-missing-block-id-list",
    level=Level.critical,
    category=Category.data_set,
    weighting=0.12,
    check_basis=CheckBasis.lines,
)

# TODO: DQSMIGRATION: Move to dqs module
StopNotInNaptanObservation = Observation(
    title="Stop not found in NaPTAN",
    text=(""),
    impacts=(
        "This observation identifies the use of stops that are not registered with NaPTAN. "
        "NaPTAN provides a source for key stop information across different transport types "
        "to support consumers to provide accurate stop information to passengers."
        + _LINE_BREAK
        + "It is important for the public transport ecosystem to work together to ensure the stop"
        " data inputted is correctly detailed and can be referenced to the NaPTAN database."
    ),
    resolve=(
        "Please notify the relevant Local Transport Authority immediately to request the stops to "
        "be registered, notifying them of issues found by this observation."
        + _LINE_BREAK
        + "For temporary stops that do not include a reference to NaPTAN, they must be defined "
        "geographically using a latitude and longitude in the data and must not be used for more than two months. "
    ),
    model=models.StopMissingNaptanWarning,
    list_url_name="dq:stop-missing-naptan-list",
    level=Level.critical,
    category=Category.stops,
    weighting=0.12,
    check_basis=CheckBasis.stops,
)
# TODO: DQSMIGRATION: Move to dqs module
FirstStopSetDownOnlyObservation = Observation(
    title="First stop is set down only",
    text=(""),
    impacts=(
        "This observation identifies journeys where the first stop is designated as set down only, "
        "meaning the bus is not scheduled to pick up passengers at the first stop. "
        + _LINE_BREAK
        + "Journey planners may not be able to show journeys with this stop correctly to passengers, "
        "disrupting their journeys."
    ),
    resolve=(
        "Please correct the stop activity on your scheduling tool or get in contact with your "
        "agent to address this observation."
    ),
    model=models.TimingPickUpWarning,
    list_url_name="dq:first-stop-set-down-only-list",
    category=Category.stops,
    level=Level.critical,
    weighting=0.10,
    check_basis=CheckBasis.timing_patterns,
)
# TODO: DQSMIGRATION: Move to dqs module
LastStopPickUpOnlyObservation = Observation(
    title="Last stop is pick up only",
    text=(""),
    impacts=(
        "This observation identifies timing patterns where the last stop is "
        "designated to be pick up only, meaning the bus is not scheduled to drop off passengers "
        "at the last stop."
        + _LINE_BREAK
        + "Journey planners may not be able to show journeys with this stop correctly "
        "to passengers, disrupting their journeys. "
    ),
    resolve=(
        "Please correct the stop details on your scheduling tool or get in contact with your "
        "agent to address this observation."
    ),
    model=models.TimingDropOffWarning,
    list_url_name="dq:last-stop-pick-up-only-list",
    level=Level.critical,
    category=Category.stops,
    weighting=0.10,
    check_basis=CheckBasis.timing_patterns,
)
MissingStopsObservation = Observation(
    title="Missing stops",
    text=(
        "This observation identifies cases where a stop may be missing from a stopping "
        "pattern from this data set provided. For example, if some journeys "
        "cover stops A, "
        "B, C and D and another journey stops at only A, B and D, stop C will "
        "be identified "
        "as a possible missing stop. If a stop is missing in the data, it cannot "
        "be show by "
        "journey planners to passengers. "
        "</br></br>"
        "Operators should investigate the observation and address any errors "
        "found."
    ),
    impacts=None,
    model=models.ServiceLinkMissingStopWarning,
    list_url_name="dq:service-link-missing-stops-list",
    level=Level.advisory,
    category=Category.stops,
)
StopsRepeatedObservation = Observation(
    title="Same stop is found multiple times",
    text=(
        "This observation identified timing patterns that feature the "
        "same stop multiple "
        "times. It is raised if a stop is included in a timing pattern four or "
        "more times. "
        "While this may not be an error, it is often caused by stringing many journeys "
        "together. "
        "</br></br>"
        "Operators should investigate the observation and address any errors found."
    ),
    model=models.TimingMultipleWarning,
    list_url_name="dq:stop-repeated-list",
    level=Level.advisory,
    category=Category.stops,
)
# TODO: DQSMIGRATION: Move to dqs module
IncorrectStopTypeObservation = Observation(
    title="Incorrect stop type",
    text=(""),
    impacts=(
        "This observation identifies the use of stops that are not designated as bus stops within NaPTAN. "
        "Expected stop types are BCT, BCQ or BCS."
        "An incorrect stop type suggested that that stop being used, is not intended for buses. "
        "This can impede the ability of passengers to be able to find the correct location to board services, "
        "particularly when planning multimodal journeys."
    ),
    resolve=(
        "Please correct the stop details on your scheduling tool or contact your Local Transport Authroity "
        "to update the stop type in NaPTAN."
    ),
    model=models.JourneyStopInappropriateWarning,
    list_url_name="dq:incorrect-stop-type-list",
    level=Level.critical,
    category=Category.stops,
    extra_info={
        "BCT": "On-street Bus / Coach / Tram Stop",
        "TXR": "Taxi Rank (head of)",
        "STR": "Shared Taxi Rank (head of)",
        "AIR": "Airport Entrance",
        "GAT": "Airport Interchange Area",
        "FTD": "Ferry Terminal / Dock Entrance",
        "FBT": "Ferry or Port Berth",
        "FER": "Ferry or Port Interchange Area",
        "RSE": "Rail Station Entrance",
        "RLY": "Railway Interchange Area",
        "RPL": "Railway Platform",
        "TMU": "Tram / Metro / Underground Entrance",
        "MET": "Underground or Metro Interchange Area",
        "PLT": "Underground or Metro platform",
        "BCE": "Bus / Coach Station Entrance",
        "BST": "Bus Coach Station Access Area",
        "BCS": "Bus / Coach bay / stand / stance within Bus / Coach Stations",
        "BCQ": "Bus Coach Station Variable Bay",
        "LCE": "Lift or Cable Car Entrance",
        "LCB": "Lift or Cable Car Access Area",
        "LPL": "Lift or Cable Car Platform",
    },
    weighting=0.10,
    check_basis=CheckBasis.stops,
)
# TODO: DQSMIGRATION: Move to dqs module
FirstStopNotTimingPointObservation = Observation(
    title="First stop is not a timing point",
    text=(""),
    impacts=(
        "This observation identifies journeys where the first stop is not set to be a timing point."
        + _LINE_BREAK
        + "A timing point is a designated stop where the bus has been registered to depart from at "
        "a specific time. The Traffic Commissioner requires registered services have the first and "
        "last stop designated as timing points. These points are where the service punctuality is "
        "monitored and is often used to generate ‘shortened’ timetables. "
        + _LINE_BREAK
        + "If the first and last stops are not timing points, the printed timetables may not display "
        "correctly and will reduce the quality of information available to passengers. "
    ),
    resolve=(
        "Please correct the stop details on your scheduling tool or get in contact with your "
        "agent to address this observation."
    ),
    model=models.TimingFirstWarning,
    list_url_name="dq:first-stop-not-timing-point-list",
    level=Level.advisory,
    category=Category.timing,
)
# TODO: DQSMIGRATION: Move to dqs module
LastStopNotTimingPointObservation = Observation(
    title="Last stop is not a timing point",
    text=(""),
    impacts=(
        "This observation identifies journeys where the last stop is not set to be a timing point. "
        + _LINE_BREAK
        + "A timing point is a designated stop where the bus has been registered to depart from at a specific time. "
        "The Traffic Commissioner requires registered services have the first and last stop designated as timing "
        "points. These points are where the service punctuality is monitored and is often used to generate "
        "‘shortened’ timetables."
        + _LINE_BREAK
        + "If the first and last stops are not timing points, the printed timetables may not display correctly"
        + "and will reduce the quality of information available to passengers. "
    ),
    resolve=(
        "Please correct the stop details on your scheduling tool or get in contact with your agent to address "
        "this observation."
    ),
    model=models.TimingLastWarning,
    list_url_name="dq:last-stop-not-timing-point-list",
    level=Level.advisory,
    category=Category.timing,
)
FastTimingPointObservation = Observation(
    title="Fast timing between timing points",
    text=(
        "This observation identifies links between timing points that "
        "appear unfeasibly "
        "fast, meaning it would require a vehicle to travel between the "
        'points as the "crow flies" at over 70mph.'
    ),
    impacts=(
        "The information provided is inaccurate and do not reflect the "
        "actual operations of "
        "the bus. This will lower the quality of data provided to passengers. "
    ),
    model=models.FastTimingWarning,
    list_url_name="dq:fast-timings-list",
    level=Level.critical,
    category=Category.timing,
    weighting=0.10,
    check_basis=CheckBasis.timing_patterns,
)
SlowTimingPointObservation = Observation(
    title="Slow timing between timing points",
    text=(
        "This observation identifies links between timing points that "
        "appear unfeasibly "
        "slow, meaning it would require a vehicle to travel between the "
        'points as the "crow flies" at a speed of less than 1 mph. This '
        "implies the data provided could be inaccurate. "
        "</br></br>"
        "Operators should investigate the observation and address any errors found."
    ),
    model=models.SlowTimingWarning,
    list_url_name="dq:slow-timings-list",
    level=Level.advisory,
    category=Category.timing,
)
FastLinkObservation = Observation(
    title="Fast running time between stops",
    text=(
        "This observation identifies links between stops that appear "
        "unfeasibly fast, "
        "meaning it would require a vehicle to travel between the stops "
        'as the "crow flies" at over 70mph. '
    ),
    impacts=(
        "The information provided is inaccurate and do not reflect the "
        "actual operation of "
        "the bus. This will lower the quality of data provided to passengers. "
    ),
    model=models.FastLinkWarning,
    list_url_name="dq:fast-link-list",
    level=Level.advisory,
    category=Category.timing,
)
SlowLinkObservation = Observation(
    title="Slow running time between stops",
    text=(
        "This observation identifies links between stops that appear unfeasibly slow, "
        "meaning it would require a vehicle to travel between the stops "
        'as the "crow flies" '
        "at a speed of less than 1 mph. This implies the data provided could be "
        "inaccurate. "
        "</br></br>"
        "Operators should investigate the observation and address any errors found."
    ),
    model=models.SlowLinkWarning,
    list_url_name="dq:slow-link-list",
    level=Level.advisory,
    category=Category.timing,
)
BackwardsTimingObservation = Observation(
    title="Backwards timing",
    text=(
        "This observation identifies timing patterns with incorrect time sequences. A "
        "timing pattern is considered to include a backwards "
        "timing if the timing of the "
        "next stop is before the current stop, or if the departure "
        "time is prior to the arrival time. "
    ),
    impacts=(
        "A backward timing indicates inaccurate scheduling, "
        "invalidating part of the route "
        "and can prevents it being displayed to passengers by journey planners. "
        "This can cause severe problems for passengers. "
    ),
    model=models.TimingBackwardsWarning,
    list_url_name="dq:backward-timing-list",
    level=Level.critical,
    category=Category.timing,
    weighting=0.12,
    check_basis=CheckBasis.timing_patterns,
)
NoTimingPointFor15MinutesObservation = Observation(
    title="No timing point for more than 15 minutes",
    text=(
        "This observation identifies timing patterns where the interval "
        "between a pair of "
        "timing points is more than 15 minutes. It is recommended by the Traffic "
        "Commissioner that services have a stop at least every 15 minutes. "
        "</br></br>"
        "Operators should investigate the observation and address any errors found."
    ),
    model=models.TimingMissingPointWarning,
    list_url_name="dq:missing-stops-list",
    level=Level.advisory,
    category=Category.timing,
)
DuplicateJourneyObservation = Observation(
    title="Duplicate journeys",
    text=(
        "This observation identifies any journeys that are included in data "
        "sets more than "
        "once. Journeys are considered to be duplicated if they have the same date "
        "range, follow the same timing pattern and have the same operating period and "
        "operating days. "
        "</br></br>"
        "Operators should investigate the observation and address any errors found."
    ),
    model=models.JourneyDuplicateWarning,
    list_url_name="dq:duplicate-journey-list",
    level=Level.advisory,
    category=Category.journey,
)
BackwardDateRangeObservation = Observation(
    title="Backward date range",
    text=(
        "This observation identifies services which have a start date "
        "later than their end "
        "date. Operators should update the date range for these routes to reflect the "
        "actual start and end dates. "
    ),
    impacts=(
        "A backward date range invalidates the route and can prevent it from being "
        "displayed to passengers by journey planners. This can cause severe problems "
        "for passengers. "
    ),
    model=models.JourneyDateRangeBackwardsWarning,
    list_url_name="dq:backward-date-range-list",
    level=Level.critical,
    category=Category.journey,
    weighting=0.12,
    check_basis=CheckBasis.vehicle_journeys,
)
JourneyOverlapObservation = Observation(
    title="Journey overlap",
    text=(
        "This observation identifies cases where journeys partially overlap. "
        "A journey is "
        "considered to partial overlap if they follow the same timing pattern "
        "for at least ten "
        "stops and there is at least one day of their operating period in which "
        "they both "
        "run. "
        "</br></br>"
        "Operators should investigate the observation and address any errors found."
    ),
    model=models.JourneyConflictWarning,
    list_url_name="dq:journey-overlap-list",
    level=Level.advisory,
    category=Category.journey,
)
ExpiredLines = Observation(
    title="Expired lines",
    text=(
        "This observation identifies any lines that have expired data associated "
        "with them. "
        "If you are uploading data please deactivate the file. "
        "If you are using a URL please remove the file from the url endpoint."
    ),
    impacts=None,
    model=LineExpiredWarning,
    list_url_name="dq:line-expired-list",
    level=Level.advisory,
    category=Category.journey,
)

OBSERVATIONS = (
    BackwardDateRangeObservation,
    BackwardsTimingObservation,
    DuplicateJourneyObservation,
    ExpiredLines,
    FastLinkObservation,
    FastTimingPointObservation,
    FirstStopNotTimingPointObservation,
    FirstStopSetDownOnlyObservation,
    IncorrectNocObservation,
    IncorrectStopTypeObservation,
    JourneyOverlapObservation,
    LastStopNotTimingPointObservation,
    LastStopPickUpOnlyObservation,
    MissingBlockNumber,
    MissingStopsObservation,
    NoTimingPointFor15MinutesObservation,
    SlowLinkObservation,
    SlowTimingPointObservation,
    StopNotInNaptanObservation,
    StopsRepeatedObservation,
)


WEIGHTED_OBSERVATIONS = [o for o in OBSERVATIONS if o.model and o.weighting]
