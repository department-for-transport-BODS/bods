import datetime
import json
import logging
import random
from datetime import timedelta
from typing import List, Optional, Tuple

import pandas as pd
import requests
from django.conf import settings

from transit_odp.avl.models import PostPublishingCheckReport, PPCReportType
from transit_odp.avl.post_publishing_checks.constants import SirivmField
from transit_odp.avl.post_publishing_checks.models import Siri, VehicleActivity
from transit_odp.avl.post_publishing_checks.weekly.constants import DailyReport
from transit_odp.timetables.csv import _get_timetable_catalogue_dataframe

logger = logging.getLogger(__name__)


class SiriHeader(dict):
    def __setitem__(self, key, value):
        if key not in SirivmField:
            raise KeyError("Key must be in SirivmField enumeration")
        dict.__setitem__(self, key, value)

    @classmethod
    def from_siri_packet(cls, siri: Siri):
        siri_header = cls()
        siri_header[SirivmField.VERSION] = siri.version
        siri_header[
            SirivmField.RESPONSE_TIMESTAMP_SD
        ] = siri.service_delivery.response_timestamp
        siri_header[SirivmField.PRODUCER_REF] = siri.service_delivery.producer_ref
        vmd = siri.service_delivery.vehicle_monitoring_delivery
        siri_header[SirivmField.RESPONSE_TIMESTAMP_VMD] = vmd.response_timestamp
        siri_header[SirivmField.REQUEST_MESSAGE_REF] = vmd.request_message_ref
        siri_header[SirivmField.VALID_UNTIL] = vmd.valid_until
        siri_header[SirivmField.SHORTEST_POSSIBLE_CYCLE] = vmd.shortest_possible_cycle
        return siri_header


class SirivmSampler:
    def get_siri_vm_data_feed_by_id(self, feed_id: int) -> Optional[bytes]:
        url = f"{settings.CAVL_CONSUMER_URL}/datafeed/{feed_id}/"
        try:
            response = requests.get(url, timeout=60)
        except requests.RequestException:
            logger.exception(f"Error requesting {url}")
            return None

        if response.status_code != 200:
            logger.error(f"Status code {response.status_code} returned from GET {url}")
            return None

        return response.content

    def get_vehicle_activities(
        self,
        feed_id: int,
        num_activities: int,
    ) -> Tuple[SiriHeader, List[VehicleActivity]]:
        random.seed()
        sirivm_fields = {}
        feed = self.get_siri_vm_data_feed_by_id(feed_id=feed_id)
        if not isinstance(feed, bytes):
            return sirivm_fields, []

        siri = Siri.from_bytes(feed)
        sirivm_header = SiriHeader.from_siri_packet(siri)

        vmd = siri.service_delivery.vehicle_monitoring_delivery

        logger.info(
            f"Client returned {len(vmd.vehicle_activities)} vehicle activities for "
            f"feed {feed_id}"
        )
        inscope_inseason_lines = self.get_inscope_inseason_lines()

        vehicle_activities = [
            vehicle_activity
            for vehicle_activity in vmd.vehicle_activities
            if vehicle_activity.monitored_vehicle_journey.line_ref
            in inscope_inseason_lines
        ]

        logger.info(
            f"In Scope and In Season vehicle activities {len(vehicle_activities)} for "
            f"feed {feed_id}"
        )

        if len(vehicle_activities) == 0:
            return sirivm_header, []

        vehicle_activities = self.ignore_old_activites(
            vehicle_activities, vmd.response_timestamp.date(), feed_id
        )

        logger.info(
            f"Vehicle activities not already analised {len(vehicle_activities)} for "
            f"feed {feed_id}"
        )

        if len(vehicle_activities) == 0:
            return sirivm_header, []

        num_samples = min(num_activities, len(vehicle_activities))
        samples = random.sample(vehicle_activities, k=num_samples)

        logger.debug(
            f"Added {len(samples)} sample vehicle activities for feed id {feed_id}"
        )

        return sirivm_header, samples

    def get_inscope_inseason_lines(self) -> set:
        """
        Retrieves a set of unique service numbers corresponding to lines that are 'In Scope' and 'In Season'
        according to the timetable catalogue.

        Returns:
            set: A set containing unique service numbers of lines that are 'In Scope' and 'In Season'.
        """
        timetable_df = _get_timetable_catalogue_dataframe()
        inscope_inseason_lines = timetable_df[
            (timetable_df["Scope Status"] == "In Scope")
            & (timetable_df["Seasonal Status"] != "Out of Season")
        ]
        inscope_inseason_lines = inscope_inseason_lines["OTC:Service Number"].str.split(
            "|", expand=True
        )
        inscope_inseason_lines = inscope_inseason_lines.melt()["value"].dropna()
        inscope_inseason_lines = set(inscope_inseason_lines)
        return inscope_inseason_lines

    def ignore_old_activites(
        self,
        activities: List[VehicleActivity],
        response_date: datetime.date,
        feed_id: int,
    ) -> List[VehicleActivity]:
        """Ignore vehicle activities which matches any of the two criterias given below
        1. If same RecordedAtTime and vehicleRef has already been processed in given week
        2. If vehicle activities RecordedAtTime (date) is different than the response date in XML

        Only dates will be compared, Time part will be ignored

        Args:
            activities (List[VehicleActivity]): list of activities extracted from XML response
            response_date (datetime.date): response date from XML response
            feed_id (int): dataset id being checked

        Returns:
            List[VehicleActivity]: List of activities which can be processed further
        """
        activities_df = self.ignore_first_timer_old_vehicle_activities(
            self.ignore_second_timer_activities(activities, feed_id), response_date
        )
        activities = []
        for index, row in activities_df.iterrows():
            activities.append(VehicleActivity(**row))

        return activities

    def ignore_first_timer_old_vehicle_activities(
        self, activities_df: pd.DataFrame, response_date: datetime.date
    ) -> pd.DataFrame:
        """Ignore the vehicle activities for which recorded_at_time != response_date

        Args:
            activities_df (pd.DataFrame): All the first time activities dataframe
            response_date (datetime.date): The response date key in Siri response

        Returns:
            pd.DataFrame: Dataframe after ignoring the first time old activities
        """
        return activities_df[activities_df["recorded_at_time"].dt.date == response_date]

    def ignore_second_timer_activities(
        self, activities: List[VehicleActivity], feed_id: int
    ) -> pd.DataFrame:
        """Ignore the vehicle activities which has already been processed
        by comparing RecordedAtDate and VehicleRef

        Args:
            activities (List[VehicleActivity]): List of Siri vehicle activities
            feed_id (int): dataset id

        Returns:
            pd.DataFrame: returns the dataframe with first time vehicle activities
        """
        prev_activities = self.get_week_reports_df(feed_id)
        curr_activities = pd.DataFrame(
            [self.format_date(activity.dict()) for activity in activities]
        )

        if prev_activities.empty:
            return curr_activities

        prev_activities["RecordedAtDate"] = pd.to_datetime(
            prev_activities["RecordedAtTime"]
        ).dt.date

        merged_df = pd.merge(
            curr_activities,
            prev_activities,
            on=["VehicleRef", "RecordedAtDate"],
            how="left",
            indicator=True,
        )

        return (
            merged_df[merged_df["_merge"] == "left_only"]
            .drop(prev_activities.columns, axis=1)
            .drop(columns="_merge")
        )

    def format_date(self, activity: dict[str, str]) -> dict[str, str]:
        """Create two columns in incoming df, to make it easier for merge

        Args:
            activity (dict[str, str]): dict object of vehicle activity

        Returns:
            dict[str, str]: dict object of vehicle activity with extra columns
        """
        activity["RecordedAtDate"] = activity["recorded_at_time"].date()
        activity["VehicleRef"] = activity["monitored_vehicle_journey"]["vehicle_ref"]
        return activity

    def get_week_reports_df(self, feed_id: int) -> pd.DataFrame:
        """Get current week old vehicle activities dataframe

        Args:
            feed_id (int): dataset id

        Returns:
            pd.DataFrame: Will have all the vehicle activities proccessed
            in the current week
        """
        if datetime.datetime.today().weekday() == 0:
            # today is Monday, so don't expect any report
            return pd.DataFrame()

        start_date, end_date = self.get_start_and_end_date()

        feeds_in_last_week = PostPublishingCheckReport.objects.filter(
            created__range=[start_date, end_date],
            granularity=PPCReportType.DAILY,
            dataset_id=feed_id,
        )

        if feeds_in_last_week.count() == 0:
            return pd.DataFrame()

        dataframes = []
        final_dataframe = pd.DataFrame()

        for report in feeds_in_last_week:
            json_report = json.load(report.file.open("rb"))
            if (
                "All SIRI-VM analysed" in json_report
                and len(json_report["All SIRI-VM analysed"]) > 0
            ):
                dataframes.append(pd.DataFrame(json_report["All SIRI-VM analysed"]))
        if len(dataframes):
            final_dataframe = pd.concat(dataframes, ignore_index=True)
        return final_dataframe

    def get_start_and_end_date(self) -> tuple[datetime.date, datetime.date]:
        """Get start and end date for old report
        in order analize vehicle activity

        Returns:
            tuple: start date and end date
        """
        end_date = datetime.datetime.today()
        start_date = self.get_prev_monday(end_date)
        if end_date.weekday() > 0:
            end_date = end_date - timedelta(days=1)
        return start_date, end_date

    def get_prev_monday(self, end_date: datetime.date) -> datetime.date:
        """Get the date on Monday in the week,
        It will act as a start date for the week

        Args:
            end_date (Date): today's date

        Returns:
            start_date (Date)
        """
        days_to_monday = end_date.weekday()
        start_date = (
            end_date
            if end_date.weekday() == 0
            else end_date - timedelta(days=days_to_monday)
        )
        return start_date
