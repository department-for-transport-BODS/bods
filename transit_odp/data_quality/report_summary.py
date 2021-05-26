from typing import Dict

from pydantic import BaseModel

from transit_odp.data_quality.constants import OBSERVATIONS, Category, Level
from transit_odp.data_quality.models import DataQualityReportSummary

CRITICAL_INTRO = (
    "These observations are considered critical in terms of data quality. "
    "An operator should aim to have zero critical observations in their data."
)
ADVISORY_INTRO = (
    "These observations suggest there may be an error in the data. "
    "However, for some types of services these may be intended by the operator. "
    "Advisory observation should be investigated and addressed."
)


class Summary(BaseModel):
    data: Dict = {}
    count: int = 0

    @classmethod
    def from_report_summary(cls, report_summary: DataQualityReportSummary):
        warning_data = {}
        total_warnings = 0
        observations = [o for o in OBSERVATIONS if o.model]

        for level in Level:
            warning_data[level.value] = {"count": 0, "categories": {}}
            for category in Category:
                warning_data[level.value]["categories"][category.value] = {
                    "count": 0,
                    "warnings": [],
                }

        for observation in observations:
            count = report_summary.data.get(observation.model.__name__, 0)
            if count > 0:
                total_warnings += count
                warning_data[observation.level.value]["count"] += count
                warning_data[observation.level.value]["categories"][
                    observation.category.value
                ]["count"] += count
                warning_data[observation.level.value]["categories"][
                    observation.category.value
                ]["warnings"].append({"count": count, "warning": observation})

        warning_data["Critical"]["intro"] = CRITICAL_INTRO
        warning_data["Advisory"]["intro"] = ADVISORY_INTRO

        return cls(data=warning_data, count=total_warnings)
