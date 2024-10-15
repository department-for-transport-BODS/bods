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


@unique
class Level(Enum):
    critical = "Critical"
    advisory = "Advisory"


@unique
class Category(Enum):
    stops = "Stop"
    timing = "Timing"
    journey = "Journey"
    data_set = "Data set"
    service = "Service"


class CheckBasis(Enum):
    stops = "stops"
    lines = "lines"
    timing_patterns = "timing_patterns"
    vehicle_journeys = "vehicle_journeys"
    data_set = "data_set"


class Checks(Enum):
    DefaultCheck = ""
    IncorrectNoc = "Incorrect NOC"
    IncorrectLicenceNumber = "Incorrect licence number"
    FirstStopIsSetDown = "First stop is set down only"
    LastStopIsPickUpOnly = "Last stop is pick up only"
    IncorrectStopType = "Incorrect stop type"
    StopNotFoundInNaptan = "Stop not found in NaPTAN"
    LastStopIsNotATimingPoint = "Last stop is not a timing point"
    FirstStopIsNotATimingPoint = "First stop is not a timing point"
    MissingJourneyCode = "Missing journey code"
    DuplicateJourneyCode = "Duplicate journey code"
    NoTimingPointMoreThan15Minutes = "No timing point for more than 15 minutes"
    MissingBusWorkingNumber = "Missing bus working number"
    MissingStop = "Missing stop"
    SameStopFoundMultipleTimes = "Same stop found multiple times"
    CancelledServiceAppearingActive = (
        "Cancelled service incorrectly appearing as active"
    )
    ServicedOrganisationOutOfDate = "Serviced organisation data is out of date"
    ServiceNumberNotMatchingRegistration = "Service number does not match registration"
    MissingData = "Missing data"
    DuplicateJourneys = "Duplicate journeys"


CHECKS_DATA = [
    {
        "observation": Checks.IncorrectNoc.value,
        "importance": Level.critical.value,
        "category": Category.data_set.value,
        "queue_name": "incorrect-noc-queue",
    },
    {
        "observation": Checks.FirstStopIsSetDown.value,
        "importance": Level.critical.value,
        "category": Category.stops.value,
        "queue_name": "first-stop-is-set-down-only-queue",
    },
    {
        "observation": Checks.LastStopIsPickUpOnly.value,
        "importance": Level.critical.value,
        "category": Category.stops.value,
        "queue_name": "last-stop-is-pickup-only-queue",
    },
    {
        "observation": Checks.FirstStopIsNotATimingPoint.value,
        "importance": Level.critical.value,
        "category": Category.timing.value,
        "queue_name": "first-stop-is-not-a-timing-point-queue",
    },
    {
        "observation": Checks.LastStopIsNotATimingPoint.value,
        "importance": Level.critical.value,
        "category": Category.timing.value,
        "queue_name": "last-stop-is-not-a-timing-point-queue",
    },
    {
        "observation": Checks.IncorrectStopType.value,
        "importance": Level.critical.value,
        "category": Category.stops.value,
        "queue_name": "incorrect-stop-type-queue",
    },
    {
        "observation": Checks.MissingJourneyCode.value,
        "importance": Level.critical.value,
        "category": Category.journey.value,
        "queue_name": "missing-journey-code-queue",
    },
    {
        "observation": Checks.DuplicateJourneyCode.value,
        "importance": Level.critical.value,
        "category": Category.journey.value,
        "queue_name": "duplicate-journey-code-queue",
    },
    {
        "observation": Checks.MissingBusWorkingNumber.value,
        "importance": Level.advisory.value,
        "category": Category.journey.value,
        "queue_name": "missing-bus-working-number-queue",
    },
    {
        "observation": Checks.MissingStop.value,
        "importance": Level.advisory.value,
        "category": Category.stops.value,
        "queue_name": "missing-stop-queue",
    },
    {
        "observation": Checks.StopNotFoundInNaptan.value,
        "importance": Level.critical.value,
        "category": Category.stops.value,
        "queue_name": "stop-not-found-in-naptan-queue",
    },
    {
        "observation": Checks.SameStopFoundMultipleTimes.value,
        "importance": Level.advisory.value,
        "category": Category.stops.value,
        "queue_name": "same-stop-found-multiple-times-queue",
    },
    {
        "observation": Checks.IncorrectLicenceNumber.value,
        "importance": Level.critical.value,
        "category": Category.data_set.value,
        "queue_name": "incorrect-licence-number-queue",
    },
]


BUS_SERVICES_AFFECTED_SUBSET = ["service_code", "line_name"]


_ANCHOR: Final = '<a class="govuk-link" target="_blank" href="{0}">{0}</a>'
_TRAVEL_LINE_ANCHOR = _ANCHOR.format(
    "https://www.travelinedata.org.uk/traveline-open-data/"
    "transport-operations/browse/"
)
_TRANSXCHANGE_ANCHOR: Final = _ANCHOR.format(
    "https://www.gov.uk/government/collections/transxchange"
)
_LINE_BREAK = "<br/><br/>"


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
    is_active: bool = True
    order: int = 1

    @property
    def type(self):
        return self.category.value


IncorrectNocObservation = Observation(
    title=Checks.IncorrectNoc.value,
    text=(
        "This observation identifies where the National Operator Code (NOC) used in the data"
        " is not registered to your BODS Organisation profile."
    ),
    impacts=(
        "NOCs are used by data consumers to know which operator is running the service, and to"
        " match the data with bus location and fares data. This ability improves the quality of"
        " information available to passengers."
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
    title=Checks.StopNotFoundInNaptan.value,
    text="This observation identifies the use of stops that are not registered with NaPTAN. ",
    impacts=(
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
    level=Level.advisory,
    category=Category.stops,
    weighting=0.12,
    check_basis=CheckBasis.stops,
)

FirstStopSetDownOnlyObservation = Observation(
    title=Checks.FirstStopIsSetDown.value,
    text=(
        "This observation identifies journeys where the first stop is designated as set down only, "
        "meaning the bus is not scheduled to pick up passengers at the first stop. "
    ),
    impacts=(
        "Journey planners may not be able to show journeys with this stop correctly to passengers, "
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
    title=Checks.LastStopIsPickUpOnly.value,
    text=(
        "This observation identifies journeys where the last stop is designated as pick up only,"
        " meaning the bus is not scheduled to set down passengers at the last stop."
    ),
    impacts=(
        "Journey planners may not be able to show journeys with this stop correctly "
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
    title=Checks.IncorrectStopType.value,
    text=(
        "This observation identifies the use of stops that are not designated as bus stops within NaPTAN. "
        "Expected stop types are BCT, BCQ, BCE, BST or BCS."
    ),
    impacts=(
        "An incorrect stop type suggests that the stop being used is not intended for buses. "
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
    title=Checks.FirstStopIsNotATimingPoint.value,
    text="This observation identifies journeys where the first stop is not set to be a timing point.",
    impacts=(
        "A timing point is a designated stop where the bus has been registered to depart from at "
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
    level=Level.critical,
    category=Category.timing,
)

LastStopNotTimingPointObservation = Observation(
    title=Checks.LastStopIsNotATimingPoint.value,
    text="This observation identifies journeys where the last stop is not set to be a timing point. ",
    impacts=(
        "A timing point is a designated stop where the bus has been registered to depart from at a specific time. "
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
    level=Level.critical,
    category=Category.timing,
)

DuplicateJourneyCodeObservation = Observation(
    title=Checks.DuplicateJourneyCode.value,
    text=(
        "This observation identifies where there are more than one vehicle journey for the same bus service that"
        " operate on the same day(s) and have the same journey code."
    ),
    impacts=(
        "Journey code is unique identifier of a vehicle journey. Without this, journey planners will not be able"
        " to match the timetables data to the equivalent location data for that service to provide passengers with"
        " predicted or calculated arrival time of a bus at a stop."
    ),
    resolve=(
        "Please enter a unique journey code on your scheduling tool for vehicle journeys operated by the same"
        " bus service and on the same day(s)."
    ),
    preamble="The following service(s) have been observed to have at least one journey that has a duplicate journey code.",
    list_url_name="dq:duplicate-journey-code-list",
    level=Level.advisory,
    category=Category.journey,
    is_active=True,
)

MissingJourneyCodeObservation = Observation(
    title=Checks.MissingJourneyCode.value,
    text="This observation identifies vehicle journeys that are missing a journey code",
    impacts=(
        "Journey code is unique identifier of a vehicle journey. Without this, journey"
        " planners will not be able to match the timetables data to the equivalent location"
        " data for that service to provide passengers with predicted or calculated arrival"
        " time of a bus at a stop. "
    ),
    resolve=(
        "Please enter a journey code on your scheduling tool for all vehicle journeys. This code will need to be unique for vehicle journeys operated by the same bus service and on the same day(s)."
    ),
    preamble="The following service(s) have been observed to have at least one journey that is missing a journey code.",
    list_url_name="dq:missing-journey-code-list",
    level=Level.critical,
    category=Category.journey,
    is_active=True,
)

CancelledServiceAppearingActiveObservation = Observation(
    title=Checks.CancelledServiceAppearingActive.value,
    text=(
        "This observation identifies services that have been cancelled or is not registered with"
        " the responsible local bus registrations authority, but the published data indicate that"
        " they are running. "
    ),
    impacts=(
        "Services that are no longer running will appear on journey planning apps causing major"
        " disruption to passengers and impacting passenger satisfaction. Operators must ensure the"
        " published data accurately reflects the status of their registered services. "
    ),
    resolve=(
        "If the service is no longer running, please remove the published file from the uploaded"
        " data set, or end date the file equal to the date the service stopped running. This can"
        " be done on your timetables scheduling tool."
        + _LINE_BREAK
        + "If the service is running, please contact the responsible local bus registrations authority"
        " to register the bus service."
    ),
    preamble="The following service(s) have been observed to not be registered with a local bus registrations authority.",
    list_url_name="dq:cancelled-service-appearing-active-list",
    level=Level.critical,
    category=Category.data_set,
    is_active=True,
)

IncorrectLicenceNumberObservation = Observation(
    title=Checks.IncorrectLicenceNumber.value,
    text=(
        "This observation identifies where licence numbers used in the data is not registered"
        " to your BODS Organisation profile."
    ),
    impacts=(
        "Licence numbers are used by data consumers to know which operator is running the service,"
        " and to match the data with bus location and fares data. This ability improves the quality"
        " of information available to passengers."
    ),
    resolve=(
        "Please check the licence number in your data is correct for your organisation and"
        " is assigned to your Organisation profile."
        + _LINE_BREAK
        + "Operators can assign a licence number to their account by going to My account"
        " (in the top right-hand side of the dashboard) and choosing Organisation profile."
    ),
    preamble="The following service(s) have been observed to not have the correct licence numbers.",
    list_url_name="dq:incorrect-licence-number-list",
    level=Level.critical,
    category=Category.data_set,
    is_active=True,
)

ServicedOrganisationOutOfDateObservation = Observation(
    title=Checks.ServicedOrganisationOutOfDate.value,
    text=(
        "This observation identifies services that have journeys operating during Serviced"
        " Organisation days that have passed."
    ),
    impacts=(
        "Serviced organisations hold dates for when organisations, such as schools, are open"
        " and closed. If the date has passed, the journeys will not appear in journey planning"
        " apps impacting passenger satisfaction. Operators must ensure the data provides reliable,"
        " up-to-date information for passengers. "
    ),
    resolve=(""),
    preamble="The following service(s) have been observed to not have the correct licence numbers.",
    list_url_name="dq:serviced-organisation-out-of-date-list",
    level=Level.advisory,
    category=Category.data_set,
    is_active=False,
)

ServiceNumberNotMatchingRegistrationObservation = Observation(
    title=Checks.ServiceNumberNotMatchingRegistration.value,
    text=(
        "This observation identifies services published with a service number that does not match the"
        " bus registrations data."
    ),
    impacts=(
        "The service number is found in the ‘LineName’ field in TransXChange"
        " and contains the public-facing name of the service. "
        + _LINE_BREAK
        + "Data consumers will display the ‘LineName’ on the front of the bus. Incorrect or abbreviated"
        " use of service numbers in the data will cause confusion for passengers. It is important that"
        " the published service number is accurate and consistent to provide reliable information to"
        " passengers."
    ),
    resolve=(""),
    preamble="The following service(s) have been observed to not have the correct licence numbers.",
    list_url_name="dq:service-number-not-matching-registration-list",
    level=Level.advisory,
    category=Category.data_set,
    is_active=False,
)

MissingDataObservation = Observation(
    title=Checks.MissingData.value,
    text=(
        "This observation identifies services that have gaps or not providing data for at least 42 days"
        " ahead of today’s date. This does not include services that are due to be cancelled with the"
        " registrations authority within the next 42 days."
    ),
    impacts=(
        "Failure to provide timetables information for future dates will impact passenger’s ability"
        " to plan their journeys in advance. "
    ),
    resolve=(""),
    preamble="The following service(s) have been observed to not have the correct licence numbers.",
    list_url_name="dq:missing-data-list",
    level=Level.advisory,
    category=Category.data_set,
    is_active=False,
)

MissingBusWorkingNumberObservation = Observation(
    title=Checks.MissingBusWorkingNumber.value,
    text=(
        "This observation identifies if the service is valid within the next 14 days, and when it is"
        " valid it contains a bus workings number."
    ),
    impacts=(
        "Bus workings number, known as ‘BlockNumber’ in TransXChange, is most frequently populated using"
        " running board information. It is a unique identifier (usually a simple number) that is used for"
        " all journeys an individual bus is scheduled to work. "
        + _LINE_BREAK
        + "This is important to enable cross journey predictions for passengers, meaning if a vehicle is"
        " running late on one journey, the subsequent journeys are likely to be delayed as well. "
    ),
    resolve=(
        "Please enter a unique journey code on your scheduling tool for vehicle journeys operated by the"
        " same bus service and on the same day(s)."
    ),
    preamble=(
        "The following service(s) have been observed to have at least one journey that is missing"
        " a bus working number."
    ),
    list_url_name="dq:missing-bus-working-number-list",
    level=Level.advisory,
    category=Category.journey,
    is_active=True,
)

DuplicateJourneysObservation = Observation(
    title=Checks.DuplicateJourneys.value,
    text=(
        "This observation identifies where journeys for the same service that have the same operating profile,"
        " departure times and route."
    ),
    impacts=(
        "It is important to ensure that the timetables information provided is accurate to improve"
        " passengers satisfaction."
    ),
    resolve=(""),
    preamble="The following service(s) have been observed to not have the correct licence numbers.",
    list_url_name="dq:duplicate-journeys-list",
    level=Level.advisory,
    category=Category.journey,
    is_active=False,
)

NoTimingPointMoreThan15MinsObservation = Observation(
    title=Checks.NoTimingPointMoreThan15Minutes.value,
    text=(
        "This observation identifies journeys where the interval between a pair of consecutive timing"
        " points is more than 15 minutes. "
    ),
    impacts=(
        "Timing points are stops along a bus route where the bus is scheduled to arrive at a specific time. "
        + _LINE_BREAK
        + "It is recommended by the Traffic Commissioner that services have a stop at least every 15 minutes."
        " It is important to ensure the departure times on published timetables is correct to avoid disruption"
        " to passengers. "
    ),
    resolve=(
        "Please investigate the observations found for the below service(s) and make the necessary updates"
        " to the departure times on your scheduling tool if required."
    ),
    preamble=(
        "The following service(s) have been observed to have at least one journey with a timing point more than"
        " 15 minutes away from the previous timing point."
    ),
    list_url_name="dq:no-timing-point-more-than-15-minutes-list",
    level=Level.advisory,
    category=Category.timing,
    is_active=True,
)

OBSERVATIONS = (
    DuplicateJourneyCodeObservation,
    FirstStopNotTimingPointObservation,
    FirstStopSetDownOnlyObservation,
    IncorrectNocObservation,
    IncorrectStopTypeObservation,
    LastStopNotTimingPointObservation,
    LastStopPickUpOnlyObservation,
    MissingJourneyCodeObservation,
    StopNotInNaptanObservation,
    CancelledServiceAppearingActiveObservation,
    IncorrectLicenceNumberObservation,
    ServicedOrganisationOutOfDateObservation,
    ServiceNumberNotMatchingRegistrationObservation,
    MissingDataObservation,
    MissingBusWorkingNumberObservation,
    DuplicateJourneysObservation,
    NoTimingPointMoreThan15MinsObservation,
)
