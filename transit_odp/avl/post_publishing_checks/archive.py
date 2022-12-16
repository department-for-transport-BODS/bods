import datetime
import io
import zipfile

from django.db.models import Subquery

from transit_odp.avl.models import PostPublishingCheckReport, PPCReportType
from transit_odp.avl.proxies import AVLDataset


class PPCArchiveCreator:
    """Creates a PPC archive, consisting of 4 weeks' worth of PPC reports
    for all active data feeds in an organisation.
    """

    def _get_datasets_for_org(self, organisation_id: int):
        """Get list of AVL data feeds within org. Exclude draft and inactive feeds.
        It's possible that PPC reports were created for a data feed within the last 4
        weeks and then the data feed was made inactive; in this case, they're not
        included.
        """
        self._avl_datasets = (
            AVLDataset.objects.filter(organisation_id=organisation_id)
            .get_active()
            .select_related("organisation")
            .select_related("live_revision")
        )

    def _set_weekly_archive_dates(self):
        """Set the archive dates to the last four Sundays"""
        today = datetime.date.today()
        last_sunday = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
        self._archive_dates = [
            last_sunday - datetime.timedelta(weeks=n) for n in range(3, -1, -1)
        ]

    def _create_weekly_zips(self):
        self._weekly_zips = []
        for archive_end in self._archive_dates:
            archive_begin = archive_end - datetime.timedelta(days=6)
            # Get all PPC reports within a given week. If everything worked normally,
            # there should be one report per data feed, created on the Sunday night.
            # We handle the irregular cases of reports on days other than Sunday, or
            # multiple reports in the same week, by choosing the report with the latest
            # date. Initially just get all the weekly reports, ordered by latest date.
            ppc_reports = (
                PostPublishingCheckReport.objects.filter(
                    granularity=PPCReportType.WEEKLY
                )
                .filter(dataset_id__in=Subquery(self._avl_datasets.values("id")))
                .filter(created__gte=archive_begin)
                .filter(created__lte=archive_end)
                .order_by("dataset_id", "-created")
            )
            weekly_buffer = io.BytesIO()
            with zipfile.ZipFile(
                weekly_buffer, mode="w", compression=zipfile.ZIP_DEFLATED
            ) as zout:
                score_count = 0
                added_dataset_ids = set()
                for report in ppc_reports:
                    # Filter out multiple reports for the same dataset. If this happens,
                    # the first in the list is chosen, which is the report with the
                    # latest date.
                    if report.dataset_id not in added_dataset_ids:
                        content = report.file.read()
                        zout.writestr(report.file.name, content)
                        if report.vehicle_activities_analysed > 0:
                            score_count += (
                                report.vehicle_activities_completely_matching
                                * 100.0
                                / report.vehicle_activities_analysed
                            )
                        added_dataset_ids.add(report.dataset_id)

            if ppc_reports.count() == 0:
                # If no PPC reports found in a given week, set the average percentage
                # score in the filename to "0", indicating 0%. The zip file for this
                # week will be empty.
                avg_score = 0
            else:
                avg_score = round(score_count / len(added_dataset_ids))
            archive_name = (
                f"week_{archive_end.strftime('%d_%m_%Y')}_all_feeds_{avg_score}.zip"
            )
            weekly_buffer.seek(0)
            self._weekly_zips.append((weekly_buffer.getvalue(), archive_name))

    def _create_four_week_archive(self):
        """Add each of the weekly zips to one container zip."""
        self._four_week_buffer = io.BytesIO()
        with zipfile.ZipFile(
            self._four_week_buffer, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as zout:
            for weekly_zip, archive_name in self._weekly_zips:
                zout.writestr(archive_name, weekly_zip)

        self._four_week_buffer.seek(0)

    def create_archive(self, organisation_id: int) -> io.BytesIO:
        self._get_datasets_for_org(organisation_id)
        self._set_weekly_archive_dates()
        self._create_weekly_zips()
        self._create_four_week_archive()
        return self._four_week_buffer
