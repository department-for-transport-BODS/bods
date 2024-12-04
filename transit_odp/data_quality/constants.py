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


OBSERVATIONS = (IncorrectNocObservation,)


WEIGHTED_OBSERVATIONS = [o for o in OBSERVATIONS if o.model and o.weighting]
