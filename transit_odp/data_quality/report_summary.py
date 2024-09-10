from typing import Dict

import pandas as pd
from django.db.models import CharField, F
from django.db.models.expressions import Value
from django.db.models.functions import (
    Cast,
    Coalesce,
    Concat,
    ExtractHour,
    ExtractMinute,
    LPad,
    Substr,
    Upper,
)
from pydantic import BaseModel
from waffle import flag_is_active

from transit_odp.data_quality.constants import OBSERVATIONS, Category, Level
from transit_odp.data_quality.models import DataQualityReportSummary
from transit_odp.dqs.constants import BUS_SERVICES_AFFECTED_SUBSET, ReportStatus, Checks
from transit_odp.dqs.models import ObservationResults

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
    Checks.FirstStopIsSetDown.value: "drop-off-only",
    Checks.LastStopIsPickUpOnly.value: "pick-up-only",
    Checks.StopNotFoundInNaptan.value: "stop-not-in-naptan",
    Checks.FirstStopIsNotATimingPoint.value: "first-stop-not-timing-point",
    Checks.LastStopIsNotATimingPoint.value: "last-stop-not-timing-point",
    Checks.IncorrectStopType.value: "incorrect-stop-type",
    Checks.MissingJourneyCode.value: "missing-journey-code",
    Checks.DuplicateJourneyCode.value: "duplicate-journey-code",
    Checks.IncorrectLicenceNumber.value: "incorrect-licence-number",
    Checks.IncorrectNoc.value: "incorrect-noc",
    Checks.NoTimingPointMoreThan15Mins.value: "no-timing-point-more-than-15-mins",
    Checks.MissingBusWorkingNumber.value: "missing-bus-working-number",
    Checks.MissingStop.value: "missing-stops",
    Checks.SameStopFoundMultipleTimes.value: "#",
    Checks.CancelledServiceAppearingActive.value: "cancelled-service-appearing-active",
    Checks.ServicedOrganisationOutOfDate.value: "#",
    Checks.ServiceNumberNotMatchingRegistration.value: "#",
    Checks.MissingData.value: "#",
    Checks.DuplicateJourneys.value: "duplicate-journeys",
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
            "journey_start_time",
            "direction",
            "stop_name",
            "is_suppressed",
        ]
        data = (
            ObservationResults.objects.filter(
                taskresults__dataquality_report_id=report_id,
                taskresults__dataquality_report__revision_id=revision_id,
                taskresults__dataquality_report__status=ReportStatus.REPORT_GENERATED.value,
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
                journey_start_time=Concat(
                    LPad(
                        Cast(
                            ExtractHour(F("vehicle_journey__start_time")),
                            output_field=CharField(),
                        ),
                        2,
                        Value("0"),
                    ),
                    Value(":"),
                    LPad(
                        Cast(
                            ExtractMinute(F("vehicle_journey__start_time")),
                            output_field=CharField(),
                        ),
                        2,
                        Value("0"),
                    ),
                ),
                direction=Concat(
                    Upper(Substr(F("vehicle_journey__direction"), 1, 1)),
                    Substr(F("vehicle_journey__direction"), 2),
                ),
                stop_name=Concat(
                    Coalesce(
                        "service_pattern_stop__naptan_stop__common_name",
                        "service_pattern_stop__txc_common_name",
                        output_field=CharField(),
                    ),
                    Value(" ("),
                    F("service_pattern_stop__naptan_stop__atco_code"),
                    Value(")"),
                ),
                stop_type=F("service_pattern_stop__naptan_stop__stop_type"),
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
            df = df[
                [
                    "importance",
                    "category",
                    "observation",
                    "journey_start_time",
                    "direction",
                    "stop_name",
                    "is_suppressed",
                ]
            ]
            df.drop_duplicates(inplace=True)
            count = len(df)
            for level in Level:
                warning_data[level.value] = {}
                warning_data[level.value]["count"] = len(
                    df[df["importance"] == level.value]
                )
            df.to_csv("dataframe.csv")

            df = (
                df.groupby(["observation", "category", "importance"])
                .agg(
                    number_of_services_affected=("journey_start_time", "size"),
                    number_of_suppressed_observation=(
                        "is_suppressed",
                        lambda is_suppressed_series: (
                            is_suppressed_series == True
                        ).sum(),
                    ),
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
                        {
                            category: df[
                                (df["category"] == category)
                                & (df["importance"] == level.value)
                            ]
                        }
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
