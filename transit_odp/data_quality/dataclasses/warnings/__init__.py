"""
Dataclasses for parsing DQS JSON report files.
"""

from typing import Dict, List

from transit_odp.data_quality.dataclasses.warnings.base import BaseWarning
from transit_odp.data_quality.dataclasses.warnings.journeys import (
    JourneyBackwardsDateRange,
    JourneyDuplicate,
    JourneyInappropriateStop,
    JourneyPartialTimingOverlap,
    JourneyStopVariant,
    JourneysWithoutHeadsign,
)
from transit_odp.data_quality.dataclasses.warnings.lines import (
    LineExpired,
    LineMissingBlockID,
)
from transit_odp.data_quality.dataclasses.warnings.stops import (
    StopIncorrectType,
    StopMissingNaptan,
    StopServiceLinkMissing,
)
from transit_odp.data_quality.dataclasses.warnings.timings import (
    TimingBackwards,
    TimingDropOff,
    TimingFast,
    TimingFastLink,
    TimingFirst,
    TimingLast,
    TimingMissingPoint15,
    TimingMultiple,
    TimingNone,
    TimingPickUp,
    TimingSlow,
    TimingSlowLink,
)

__all__ = [
    "BaseWarning",
    "JourneyBackwardsDateRange",
    "JourneyDuplicate",
    "JourneyInappropriateStop",
    "JourneyPartialTimingOverlap",
    "JourneyStopVariant",
    "JourneysWithoutHeadsign",
    "LineExpired",
    "LineMissingBlockID",
    "StopIncorrectType",
    "StopMissingNaptan",
    "StopServiceLinkMissing",
    "TimingBackwards",
    "TimingDropOff",
    "TimingFast",
    "TimingFastLink",
    "TimingFirst",
    "TimingLast",
    "TimingMissingPoint15",
    "TimingMultiple",
    "TimingNone",
    "TimingPickUp",
    "TimingSlow",
    "TimingSlowLink",
    "WarningFactory",
]


class WarningFactory:
    def __init__(self):
        self._warnings: Dict[str, BaseWarning] = {}

    def register_warning(self, warning_type: str, warning: BaseWarning):
        self._warnings[warning_type] = warning

    def get_warning(self, warning_type: str) -> BaseWarning:
        warning = self._warnings.get(warning_type)
        if not warning:
            raise ValueError(warning_type)
        return warning

    def build(self, warning) -> List[BaseWarning]:
        type_ = warning["warning_type"]
        values = warning["values"]
        try:
            WarningClass = self.get_warning(type_)
        except ValueError:
            return []
        else:
            objs = []
            for v in values:
                # DQS removed warning_id older versions still have the id
                # lets make sure we don't try to pass it to the class
                v.pop("warning_id", None)
                objs.append(WarningClass(**v))
            return objs


factory = WarningFactory()
factory.register_warning("journey-date_range-backwards", JourneyBackwardsDateRange)
factory.register_warning("journey-duplicate", JourneyDuplicate)
factory.register_warning("journey-partial-timing-overlap", JourneyPartialTimingOverlap)
factory.register_warning("journey-stop_inappropriate", JourneyInappropriateStop)
factory.register_warning("journey-stop_variant", JourneyStopVariant)
factory.register_warning("journeys-without-headsign", JourneysWithoutHeadsign)
factory.register_warning("line-expired", LineExpired)
factory.register_warning("line-missing-block-id", LineMissingBlockID)
factory.register_warning("service-link-missing-stops", StopServiceLinkMissing)
factory.register_warning("stop-incorrect-type", StopIncorrectType)
factory.register_warning("stop-missing-naptan", StopMissingNaptan)
factory.register_warning("timing-backwards", TimingBackwards)
factory.register_warning("timing-drop_off", TimingDropOff)
factory.register_warning("timing-fast", TimingFast)
factory.register_warning("timing-fast-link", TimingFastLink)
factory.register_warning("timing-first", TimingFirst)
factory.register_warning("timing-last", TimingLast)
factory.register_warning("timing-missing-point-15", TimingMissingPoint15)
factory.register_warning("timing-multiple", TimingMultiple)
factory.register_warning("timing-none", TimingNone)
factory.register_warning("timing-pick_up", TimingPickUp)
factory.register_warning("timing-slow", TimingSlow)
factory.register_warning("timing-slow-link", TimingSlowLink)
