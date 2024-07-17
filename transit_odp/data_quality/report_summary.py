from typing import Dict

from pydantic import BaseModel

from transit_odp.data_quality.constants import OBSERVATIONS, Category, Level
from transit_odp.data_quality.models import DataQualityReportSummary
from transit_odp.dqs.models import ObservationResults
import pandas as pd
from django.db.models import F
from waffle import flag_is_active

CRITICAL_INTRO = (
    "These observations are considered critical in terms of data quality. "
    "An operator should aim to have zero critical observations in their data.!!"
)
ADVISORY_INTRO = (
    "These observations suggest there may be an error in the data. "
    "However, for some types of services these may be intended by the operator. "
    "Advisory observations should be investigated and addressed."
)

BUS_SERVICES_AFFECTED_SUBSET = ["service_code", "line_name"]

# TODO: DQSMIGRATION: REMOVE
class Summary(BaseModel):
    
    data: Dict = {}
    count: int = 0
    bus_services_affected: int = 0

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

    @classmethod
    def get_dataframe_report(cls, report_id, revision_id):
        columns = [
            "importance",
            "category",
            "observation",
            "service_code",
            "details",
            "line_name",
            "vehicle_journey_id",
        ]
        data = (
            ObservationResults.objects.filter(
                taskresults__dataquality_report_id=19,
                taskresults__dataquality_report__revision_id=36,
            )
            .annotate(
                details_annotation=F("details"),
                dd_vehicle_journey_id=F("vehicle_journey_id"),
                importance=F("taskresults__checks__importance"),
                category=F("taskresults__checks__category"),
                observation=F("taskresults__checks__observation"),
                service_code=F(
                    "taskresults__transmodel_txcfileattributes__service_code"
                ),
                line_name=F(
                    "taskresults__transmodel_txcfileattributes__service_txcfileattributes__name"
                ),
            )
            .values(*columns)
        )
        print("Printing the query of the report")
        print(data.query)
        return pd.DataFrame(data)

    @classmethod
    def get_report(cls, report_summary: DataQualityReportSummary, revision_id):
        if not flag_is_active(
        "", "is_new_data_quality_service_active"
            ):
            return cls.initialize_warning_data()
        
        if revision_id is None:
            return cls(data=cls.initialize_warning_data(), count=0)
        warning_data = {}
        try:
            df = cls.get_dataframe_report(report_summary.report_id, revision_id)
            if df.empty:
                return cls(data=cls.initialize_warning_data(), count=0)
            bus_services_affected = cls.qet_service_code_line_name_unique_combinations(
                df
            )
            df = df[["importance", "category", "observation", "vehicle_journey_id"]]
            count = len(df)
            for level in Level:
                warning_data[level.value] = {}
                warning_data[level.value]["count"] = len(
                    df[df["importance"] == level.value]
                )

            df = (
                df.groupby(["observation", "category", "importance"])
                .agg(
                    {
                        "vehicle_journey_id": "size",
                    }
                )
                .rename(
                    columns={
                        "vehicle_journey_id": "number_of_services_affected",
                    }
                )
                .reset_index()
            )

            for level in Level:
                warning_data[level.value] = {}
                warning_data[level.value]["count"] = df[
                    df["importance"] == level.value
                ]["number_of_services_affected"].sum()
                importance_df = df[df["importance"] == level.value]
                warning_data[level.value]["df"] = {}
                warning_data[level.value]["intro"] = (
                    CRITICAL_INTRO if level.value == "Critical" else ADVISORY_INTRO
                )
                for category in importance_df["category"].unique():
                    warning_data[level.value]["df"].update(
                        {category: df[df["category"] == category]}
                    )
            return cls(
                data=warning_data,
                count=count,
                bus_services_affected=bus_services_affected,
            )
        except Exception as e:
            print(e)
            # reset warning_data
            return cls(data=cls.initialize_warning_data(), count=0)

    @classmethod
    def initialize_warning_data(cls):
        warning_data = {}
        for level in Level:
            warning_data[level.value] = {}
            warning_data[level.value]["intro"] = (
                CRITICAL_INTRO if level.value == "Critical" else ADVISORY_INTRO
            )
            warning_data[level.value]["count"] = 0
        print("WARNING DATA!!!!!")
        print(warning_data)
        return warning_data

    @classmethod
    def qet_service_code_line_name_unique_combinations(cls, df):
        try:
            df = df.drop_duplicates(subset=BUS_SERVICES_AFFECTED_SUBSET)
            return len(df)
        except Exception as e:
            print(e)
