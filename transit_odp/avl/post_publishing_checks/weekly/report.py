import logging
from collections import defaultdict
from datetime import date, timedelta
from ddtrace import tracer

from django.core.files import File

from transit_odp.avl.models import PostPublishingCheckReport, PPCReportType
from transit_odp.avl.post_publishing_checks.weekly.archiver import (
    WeeklyPPCReportArchiver,
)
from transit_odp.avl.post_publishing_checks.weekly.summary import (
    AggregatedDailyReports,
    PostPublishingChecksSummaryData,
)

logger = logging.getLogger(__name__)


class WeeklyReport:
    """
    Generates Weekly PPC report by aggregating daily PPC reports from last 7 days.
    As the result the ZIP file is created which contains multiple CSVs
    with aggregated data.
    """

    def __init__(self, start_date: date = date.today()) -> None:
        self.start_date = start_date
        self.end_date = start_date - timedelta(days=6)

    @tracer.wrap(
        service="task_weekly_assimilate_post_publishing_check_reports",
        resource="generate",
    )
    def generate(self) -> None:
        """Generate summary PPC report based on start_date - 1 week range of data."""

        logger.info(
            f"Generating PPC weekly report for week {self.end_date} - {self.start_date}"
        )
        weekly_ppc_summary = PostPublishingChecksSummaryData(
            self.start_date, self.end_date
        )

        for feed_id, daily_reports in self._fetch_data().items():
            logger.info(f"Aggregating data for feed_id: {feed_id}")
            summary = weekly_ppc_summary.aggregate_daily_reports(daily_reports)

            logger.debug("Creating ZIP file...")
            zip = self._create_zip(feed_id, summary)

            logger.debug("Saving weekly report in db...")
            self._save_weekly_report(feed_id, summary, zip)

        logger.info("Weekly PPC report done.")

    def _save_weekly_report(
        self, feed_id: int, summary: AggregatedDailyReports, zip_file: File
    ) -> None:
        report, created = PostPublishingCheckReport.objects.get_or_create(
            dataset_id=feed_id,
            created=date.today(),
            granularity=PPCReportType.WEEKLY,
        )
        if not created:
            logger.warn(
                f"Weekly report already exists for week {self.start_date} for "
                f"feed {feed_id}. It's going to be overriden."
            )

        report.vehicle_activities_analysed = summary.total_vehicles_analysed
        report.vehicle_activities_completely_matching = (
            summary.total_vehicles_completely_matching
        )
        report.file = zip_file
        report.save()
        logger.info("Weekly report saved.")

    def _create_zip(self, feed_id: int, summary: AggregatedDailyReports) -> File:
        """
        Creates zip file containing bunch of CSVs generated from summary data for feed.
        """
        filename = (
            f"week_{self.start_date.strftime('%d_%m_%Y')}_feed_{feed_id}"
            f"_{summary.all_fields_matching_vehicles_score}.zip"
        )
        archiver = WeeklyPPCReportArchiver()
        archive = archiver.to_zip(summary)
        file_ = File(archive, name=filename)
        logger.info(f"ZIP file: {filename} created.")

        return file_

    def _fetch_data(self) -> dict[int, list[PostPublishingCheckReport]]:
        """
        Returns dictionary with feed_id as a key and list of daily reports
        for that feed done in last week.

        {
            feed_id: [daily_report_monday, daily_report_tuesday, ...],
            ...
        }
        """
        feeds_in_last_week = PostPublishingCheckReport.objects.filter(
            created__range=[self.end_date, self.start_date],
            granularity=PPCReportType.DAILY,
        )

        response = defaultdict(list)
        for row in feeds_in_last_week:
            response[row.dataset_id].append(row)

        if not response:
            logger.warn("No daily reports found to summarise!")

        return response
