from enum import Enum
from dataclasses import dataclass
from enum import Enum, unique
from typing import Dict, Final, Optional

class TaskResultsStatus(Enum):
    PENDING = "PENDING"


class ReportStatus(Enum):
    PIPELINE_PENDING = "PIPELINE_PENDING"
    PIPELINE_SUCCEEDED = "PIPELINE_SUCCEEDED"
    REPORT_GENERATED = "REPORT_GENERATED"
    REPORT_GENERATION_FAILED = "REPORT_GENERATION_FAILED"


CHECKS_DATA = [
    {
        "observation": "Incorrect NOC",
        "importance": "Critical",
        "category": "Data set",
        "queue_name": "incorrect-noc-queue",
    },
    {
        "observation": "First stop is set down only",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "first-stop-is-set-down-only-queue",
    },
    {
        "observation": "Last stop is pick up only",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "last-stop-is-pickup-only-queue",
    },
    {
        "observation": "First stop is not a timing point",
        "importance": "Critical",
        "category": "Timing",
        "queue_name": "first-stop-is-not-a-timing-point-queue",
    },
    {
        "observation": "Last stop is not a timing point",
        "importance": "Critical",
        "category": "Timing",
        "queue_name": "last-stop-is-not-a-timing-point-queue",
    },
    {
        "observation": "Incorrect stop type",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "incorrect-stop-type-queue",
    },
    {
        "observation": "Missing journey code",
        "importance": "Critical",
        "category": "Journey",
        "queue_name": "missing-journey-code-queue",
    },
    {
        "observation": "Duplicate journey code",
        "importance": "Critical",
        "category": "Journey",
        "queue_name": "duplicate-journey-code-queue",
    },
    {
        "observation": "Missing bus working number",
        "importance": "Advisory",
        "category": "Journey",
        "queue_name": "missing-bus-working-number-queue",
    },
    {
        "observation": "Missing stop",
        "importance": "Advisory",
        "category": "Stop",
        "queue_name": "missing-stop-queue",
    },
    {
        "observation": "Stop not found in NaPTAN",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "stop-not-found-in-naptan-queue",
    },
    {
        "observation": "Same stop found multiple times",
        "importance": "Advisory",
        "category": "Stop",
        "queue_name": "same-stop-found-multiple-times-queue",
    },
    {
        "observation": "Incorrect licence number",
        "importance": "Critical",
        "category": "Data set",
        "queue_name": "incorrect-licence-number-queue",
    },
]


BUS_SERVICES_AFFECTED_SUBSET = ["service_code", "line_name"]


class Checks(Enum):
    DefaultCheck = ""
    IncorrectNoc = "Incorrect NOC"
    FirstStopIsSetDown = "First stop is set down only"
    LastStopIsPickUpOnly = "Last stop is pick up only"
    IncorrectStopType = "Incorrect stop type"
    StopNotFoundInNaptan = "Stop not found in NaPTAN"
    LastStopIsNotATimingPoint = "Last stop is not a timing point"
    FirstStopIsNotATimingPoint = "First stop is not a timing point"


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
    extra_info: Optional[Dict[str, str]] = None
    impacts: str = None
    weighting: float = None
    check_basis: CheckBasis = None
    resolve: str = None
    preamble: str = None

    @property
    def type(self):
        return self.category.value


IncorrectNocObservation = Observation(
    title="Incorrect NOC",
    text="",
    impacts=(
        "This observation identifies where the National Operator Code (NOC) used in the data is not registered to the your Organisation profile."
        + _LINE_BREAK
        + "NOCs are used by data consumers to know which operator is running the service, and to match the data with bus location and fares data. This ability improves the quality of information available to passengers."
    ),
    resolve=(
        "Please check the NOC(s) on your data is correct for your organisation and is assigned to your Organisation profile."
        + _LINE_BREAK
        + "Operators can find their organisation’s NOC by browsing the Traveline NOC database here: "
        + _TRAVEL_LINE_ANCHOR
        + _LINE_BREAK
        + "Operators can assign a NOC to their account by going to My account (in the top right-hand side of the dashboard) and choosing Organisation profile."
    ),
    preamble="The following service(s) have been observed to have incorrect national operator code(s).",
    list_url_name="dq:incorrect-noc-list",
    level=Level.critical,
    category=Category.data_set,
    weighting=0.12,
    check_basis=CheckBasis.data_set,
)

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
    preamble="The following service(s) have been observed to have a stop that is not registered with NaPTAN.",
    list_url_name="dq:stop-missing-naptan-list",
    level=Level.critical,
    category=Category.stops,
    weighting=0.12,
    check_basis=CheckBasis.stops,
)

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
    preamble="The following service(s) have been observed to have first stop as set down only.",
    list_url_name="dq:first-stop-set-down-only-list",
    category=Category.stops,
    level=Level.critical,
    weighting=0.10,
    check_basis=CheckBasis.timing_patterns,
)

LastStopPickUpOnlyObservation = Observation(
    title="Last stop is pick up only",
    text=(""),
    impacts=(
        "This observation identifies journeys where the last stop is "
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
    preamble="The following service(s) have been observed to have last stop as pick up only.",
    list_url_name="dq:last-stop-pick-up-only-list",
    level=Level.critical,
    category=Category.stops,
    weighting=0.10,
    check_basis=CheckBasis.timing_patterns,
)

IncorrectStopTypeObservation = Observation(
    title="Incorrect stop type",
    text=(""),
    impacts=(
        "This observation identifies the use of stops that are not designated as bus stops within NaPTAN. "
        "Expected stop types are BCT, BCQ or BCS."
        + _LINE_BREAK
        + "An incorrect stop type suggests that the stop being used is not intended for buses. "
        "This can impede the ability of passengers to be able to find the correct location to board services, "
        "particularly when planning multimodal journeys."
    ),
    resolve=(
        "Please correct the stop details on your scheduling tool or contact your Local Transport Authroity "
        "to update the stop type in NaPTAN."
    ),
    preamble="The following service(s) have been observed to not have the correct stop type.",
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
    preamble="The following service(s) have been observed to not have the first stop set as a timing point.",
    list_url_name="dq:first-stop-not-timing-point-list",
    level=Level.advisory,
    category=Category.timing,
)

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
        + "If the first and last stops are not timing points, the printed timetables may not display correctly "
        + "and will reduce the quality of information available to passengers. "
    ),
    resolve=(
        "Please correct the stop details on your scheduling tool or get in contact with your agent to address "
        "this observation."
    ),
    preamble="The following service(s) have been observed to not have the last stop set as a timing point.",
    list_url_name="dq:last-stop-not-timing-point-list",
    level=Level.advisory,
    category=Category.timing,
)
