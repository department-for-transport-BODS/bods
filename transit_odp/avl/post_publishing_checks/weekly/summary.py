import json
import logging
from datetime import date
from functools import cache, cached_property

import pandas as pd

from transit_odp.avl.models import PostPublishingCheckReport
from transit_odp.avl.post_publishing_checks.weekly.constants import DailyReport
from transit_odp.avl.post_publishing_checks.weekly.fields import (
    BLOCK_REF_FIELDS,
    DESTINATION_REF_FIELDS,
    DIRECTION_REF_FIELDS,
    ORIGIN_REF_FIELDS,
    PPC_SUMMARY_FIELDS,
    SIRI_MSG_ANALYSED_FIELDS,
    UNCOUNTED_VEHICLE_ACTIVITIES_FIELDS,
)

logger = logging.getLogger(__name__)


class AggregatedDailyReports:
    """
    Class responsible for storing DataFrames for PPC weekly report for single Feed.
    """

    ppc_summary_report = pd.DataFrame(columns=PPC_SUMMARY_FIELDS)
    siri_message_analysed = pd.DataFrame(columns=SIRI_MSG_ANALYSED_FIELDS)
    uncounted_vehicle_activities = pd.DataFrame(
        columns=UNCOUNTED_VEHICLE_ACTIVITIES_FIELDS
    )
    direction_ref = pd.DataFrame(columns=DIRECTION_REF_FIELDS)
    destination_ref = pd.DataFrame(columns=DESTINATION_REF_FIELDS)
    origin_ref = pd.DataFrame(columns=ORIGIN_REF_FIELDS)
    block_ref = pd.DataFrame(columns=BLOCK_REF_FIELDS)

    total_vehicles_analysed = 0
    total_vehicles_completely_matching = 0

    @cached_property
    def all_fields_matching_vehicles_score(self) -> int:
        try:
            return (
                self.total_vehicles_completely_matching
                * 100
                // self.total_vehicles_analysed
            )
        except ZeroDivisionError:
            logger.warn("No vehicles analysed. Setting all fields matching score to 0")
            return 0

    def _remove_percentage_sign(self) -> None:
        """
        Removes % from values of following columns:
        %populated, %match, Successful match with TXC
        """
        columns_with_percentage = ["%populated", "%match", "Successful match with TXC"]

        for col in columns_with_percentage:
            self.ppc_summary_report[col] = (
                self.ppc_summary_report[col]
                .str.replace("%", "")
                .replace("-", "0")
                .astype(float)
                .astype(int)
            )

    @cache
    def _aggregate_summary_reports(self) -> pd.DataFrame:
        """Aggregates all entries from Daily PPC Report into one."""
        self._remove_percentage_sign()

        agg_df = self.ppc_summary_report.groupby(
            ["SIRI field", "TXC match field"], as_index=False
        ).agg(
            total_activities_analysed=pd.NamedAgg(
                column="Total vehicleActivities analysed", aggfunc="sum"
            ),
            total_count_siri_fields=pd.NamedAgg(
                column="Total count of SIRI fields populated", aggfunc="sum"
            ),
            successful_match_with_txc=pd.NamedAgg(
                column="Successful match with TXC",
                aggfunc="sum",
            ),
            notes=pd.NamedAgg(column="Notes", aggfunc="first"),
        )

        agg_df["%match"] = (
            agg_df["successful_match_with_txc"]
            * 100
            // agg_df["total_activities_analysed"]
        ).fillna("0").astype(str) + "%"
        agg_df["%populated"] = (
            agg_df["total_count_siri_fields"]
            * 100
            // agg_df["total_activities_analysed"]
        ).fillna("0").astype(str) + "%"

        return agg_df

    def get_summary_report(self):
        """Produces DataFrame used for avl_to_timetable_match_summary.csv."""
        df:pd.DataFrame = self._aggregate_summary_reports()

        df = pd.concat([df, pd.DataFrame([{
                "SIRI field": "Completely matched ALL elements with "
                "timetable data (excluding BlockRef)",
                "successful_match_with_txc": self.total_vehicles_completely_matching,
                "%match": f"{self.all_fields_matching_vehicles_score}%",
            }])], ignore_index=True
        )

        df = df.rename(
            columns={
                "total_activities_analysed": "Total vehicleActivities analysed",
                "total_count_siri_fields": "Total count of SIRI fields populated",
                "successful_match_with_txc": "Successful match with TXC",
                "notes": "Notes",
            }
        ).fillna("-")

        # Reorder all fields + exclude 'LineRef' field
        df = pd.concat([df.loc[0:3], df.loc[5:]]).loc[[5, 7, 1, 2, 6, 3, 0, 8]]

        cols = list(PPC_SUMMARY_FIELDS.keys())

        return df[cols]

    def get_siri_message_analysed(self) -> pd.DataFrame:
        """Produces DataFrame used for all_siri_vm_analysed.csv"""
        return self.siri_message_analysed.fillna("-")

    def get_uncounted_vehicle_activities(self) -> pd.DataFrame:
        """Produces DataFrame used for uncountedvehicleactivities.csv."""
        return self.uncounted_vehicle_activities.fillna("-")

    def get_direction_ref(self) -> pd.DataFrame:
        """Produces DataFrame used for directionref.csv."""
        return self.direction_ref.fillna("-")

    def get_destination_ref(self) -> pd.DataFrame:
        """Produces DataFrame used for destinationref.csv."""
        return self.destination_ref.fillna("-")

    def get_origin_ref(self) -> pd.DataFrame:
        """Produces DataFrame used for originref.csv."""
        return self.origin_ref.fillna("-")

    def get_block_ref(self) -> pd.DataFrame:
        """Produces DataFrame used for blockref.csv."""
        return self.block_ref.fillna("-")


class PostPublishingChecksSummaryData:
    def __init__(self, start_date: date, end_date: date) -> None:
        self.start_date = start_date
        self.end_date = end_date

    def aggregate_daily_reports(
        self, daily_reports: list[PostPublishingCheckReport]
    ) -> AggregatedDailyReports:
        summary = AggregatedDailyReports()

        for report in daily_reports:
            summary.total_vehicles_analysed += report.vehicle_activities_analysed or 0
            summary.total_vehicles_completely_matching += (
                report.vehicle_activities_completely_matching or 0
            )

            report = DailyReport(**json.load(report.file.open("rb")))

            df = pd.DataFrame(report.summary)
            summary.ppc_summary_report = pd.concat([summary.ppc_summary_report, df], ignore_index=True)

            df = pd.DataFrame(report.all_siri_analysed)
            summary.siri_message_analysed = pd.concat([summary.siri_message_analysed, df], ignore_index=True)

            df = pd.DataFrame(report.uncounted_vehicles)
            summary.uncounted_vehicle_activities = pd.concat([summary.uncounted_vehicle_activities, df], ignore_index=True)

            df = pd.DataFrame(report.direction_ref)
            summary.direction_ref = pd.concat([summary.direction_ref, df], ignore_index=True)

            df = pd.DataFrame(report.destination_ref)
            summary.destination_ref = pd.concat([summary.destination_ref, df], ignore_index=True)

            df = pd.DataFrame(report.origin_ref)
            summary.origin_ref = pd.concat([summary.origin_ref, df], ignore_index=True)

            df = pd.DataFrame(report.block_ref)
            summary.block_ref = pd.concat([summary.block_ref, df], ignore_index=True)

        return summary
