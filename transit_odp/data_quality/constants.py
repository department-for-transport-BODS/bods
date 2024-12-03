from dataclasses import dataclass
from enum import Enum, unique
from typing import Dict, Final, Optional

from transit_odp.data_quality import models
from transit_odp.dqs.constants import Level, Category


_ANCHOR: Final = '<a class="govuk-link" target="_blank" href="{0}">{0}</a>'
_TRAVEL_LINE_ANCHOR = _ANCHOR.format(
    "https://www.travelinedata.org.uk/traveline-open-data/"
    "transport-operations/browse/"
)
_TRANSXCHANGE_ANCHOR: Final = _ANCHOR.format(
    "https://www.gov.uk/government/collections/transxchange"
)
_LINE_BREAK = "<br/><br/>"


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
    preamble: str = None
    is_active: bool = True

    @property
    def type(self):
        return self.category.value


IncorrectNocObservation = Observation(
    title="Incorrect NOC",
    text=(
        "Operators can find their organisation’s NOC by browsing the Traveline NOC "
        "database here:"
        "</br></br>" + _TRAVEL_LINE_ANCHOR + "</br></br>"
        "Operators can assign a NOC to their account on this service by going to My "
        "account (in the top right-hand side of the dashboard) and choosing "
        "Organisation profile. "
    ),
    impacts=(
        "The NOC is used by consumers to know which operator is running the service, "
        "and to match their data across data types. This ability improves "
        "the quality of information available to passengers."
    ),
    preamble="The following data sets have been observed to have incorrect national operator code(s).",
    model=models.IncorrectNOCWarning,
    list_url_name="dq:incorrect-noc-list",
    level=Level.critical,
    category=Category.data_set,
    weighting=0.12,
    check_basis=CheckBasis.data_set,
)


IncorrectStopTypeObservation = Observation(
    title="Incorrect stop type",
    text=(
        "Stopping patterns are considered to be using stops of the incorrect"
        " type if the "
        "stops are not designated at bus stops within NaPTAN. Stopping patterns are "
        "considered to be using stops of the incorrect type if the stops are not "
        "designated as bus stops within NaPTAN. Expected stop types are BCT, BCQ "
        "or BCS."
    ),
    impacts=(
        "An incorrect stop type suggested that that stop being used, is not "
        "intended for "
        "buses. This can impede the ability of passengers to be able to find "
        "the correct "
        "location to board services, particularly when planning multimodal journeys. "
    ),
    preamble="Following timing pattern(s) have been observed to have incorrect stop type.",
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

OBSERVATIONS = (
    BackwardDateRangeObservation,
    IncorrectNocObservation,
    IncorrectStopTypeObservation,
)


WEIGHTED_OBSERVATIONS = [o for o in OBSERVATIONS if o.model and o.weighting]
