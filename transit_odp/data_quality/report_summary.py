from typing import Dict

from pydantic import BaseModel

from transit_odp.data_quality.constants import OBSERVATIONS, Category, Level
from transit_odp.data_quality.models import DataQualityReportSummary
from transit_odp.dqs.models import ObservationResults
import pandas as pd
from django.db.models import F
from waffle import flag_is_active
from transit_odp.dqs.constants import BUS_SERVICES_AFFECTED_SUBSET, ReportStatus
CRITICAL_INTRO = (
    "These observations are considered critical in terms of data quality. "
    "An operator should aim to have zero critical observations in their data."
)
ADVISORY_INTRO = (
    "These observations suggest there may be an error in the data. "
    "However, for some types of services these may be intended by the operator. "
    "Advisory observations should be investigated and addressed."
)

URL_MAPPING = {
    "First stop is set down only": "drop-off-only",
    "Last stop is pick up only": "pick-up-only",
    "Stop not found in NaPTAN": "stop-not-in-naptan",
}


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
        """Get the data quality report as a pandas dataframe
        by report_id and revision_id
        Returns:
            DF : DataFrame contains the data quality report or empty DataFrame
        """
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
                taskresults__dataquality_report_id=report_id,
                taskresults__dataquality_report__revision_id=revision_id,
                taskresults__dataquality_report__status=ReportStatus.PIPELINE_SUCCEEDED.value,
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
        return pd.DataFrame(data)

    @classmethod
    def get_report(cls, report_id, revision_id):
        """Generate a summary of the data quality report
        Functionality:
        - Check if the is_new_data_quality_service_active flag is active,
          then it will return empty warning data report.
        - Get the data quality report as a pandas dataframe by report_id and revision_id
        - If the dataframe is empty, then it will return empty warning data report.
        - Get the unique combinations of service_code and line_name
        - Group the dataframe by observation, category, and importance
        - Count the number of services affected by the observation
        - Create a dictionary of warning data
        - Return the warning data report


        Returns:
            class instance with data as the warning data report, and count of all warnings.
        """

        if (
            report_id is None
            or revision_id is None
            or not flag_is_active("", "is_new_data_quality_service_active")
        ):
            return cls(data=cls.initialize_warning_data(), count=0)
        warning_data = {}
        try:
            df = cls.get_dataframe_report(report_id, revision_id)
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
            # Add column on the df for the url from the url mapping, if the obeervation is not in mapping use None
            df["url"] = df["observation"].map(URL_MAPPING)
            # change nan to no-url in url column only
            df["url"] = df["url"].fillna("no-url")
            for level in Level:
                warning_data[level.value] = {}
                warning_data[level.value]["count"] = df[
                    df["importance"] == level.value
                ]["number_of_services_affected"].sum()
                importance_df = df[df["importance"] == level.value]
                # TODO: change df to something like data, or better name in the dict
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
        return warning_data

    @classmethod
    def qet_service_code_line_name_unique_combinations(cls, df):
        try:
            df = df.drop_duplicates(subset=BUS_SERVICES_AFFECTED_SUBSET)
            return len(df)
        except Exception as e:
            print(e)
