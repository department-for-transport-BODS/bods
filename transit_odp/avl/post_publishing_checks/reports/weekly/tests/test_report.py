from datetime import date, timedelta
from unittest.mock import Mock, PropertyMock, patch

import pytest
from django.core.files.base import ContentFile
from freezegun import freeze_time

from transit_odp.avl.factories import PPCReportFactory
from transit_odp.avl.models import PostPublishingCheckReport, PPCReportType
from transit_odp.avl.post_publishing_checks.reports import WeeklyReport
from transit_odp.organisation.factories import DatasetFactory

pytestmark = pytest.mark.django_db
mock_path_prefix = "transit_odp.avl.post_publishing_checks.reports.weekly.report."
FetchedDataType = dict[int, list[PostPublishingCheckReport]]
TEST_DATE = "2022-10-30"


@pytest.fixture()
@freeze_time(TEST_DATE)
def mockup_reports() -> FetchedDataType:
    dataset = DatasetFactory()

    daily_reports_dates = [
        date(2022, 10, 30) + timedelta(days=1),
        date(2022, 10, 30),
        date(2022, 10, 30) - timedelta(days=1),
        date(2022, 10, 30) - timedelta(days=2),
        date(2022, 10, 30) - timedelta(days=3),
        date(2022, 10, 30) - timedelta(days=4),
        date(2022, 10, 30) - timedelta(days=5),
        date(2022, 10, 30) - timedelta(days=6),
        date(2022, 10, 30) - timedelta(days=7),
        date(2022, 10, 30) - timedelta(days=8),
    ]

    reports = []
    for date_ in daily_reports_dates:
        reports.append(PPCReportFactory(dataset=dataset, created=date_))

    return {reports[0].dataset_id: reports}


@pytest.fixture()
def summary_mock() -> Mock:
    score_mock = PropertyMock(return_value=60)

    summary_mock = Mock()
    type(summary_mock).all_fields_matching_vehicles_score = score_mock
    type(summary_mock).total_vehicles_analysed = score_mock
    type(summary_mock).total_vehicles_completely_matching = score_mock

    return summary_mock


@freeze_time(TEST_DATE)
def test_weekly_report_init_with_correct_dates() -> None:
    wr = WeeklyReport(start_date=date.today())

    assert wr.start_date.strftime("%Y-%m-%d") == "2022-10-30"
    assert wr.end_date.strftime("%Y-%m-%d") == "2022-10-24"


@freeze_time(TEST_DATE)
@patch(mock_path_prefix + "PostPublishingChecksSummaryData.aggregate_daily_reports")
def test_saving_weekly_report(
    agg_reports_mock: Mock, mockup_reports: FetchedDataType, summary_mock: Mock
) -> None:
    agg_reports_mock.return_value = summary_mock

    wr = WeeklyReport(start_date=date.today())
    wr._fetch_data = Mock(return_value=mockup_reports)
    wr._create_zip = Mock(return_value=ContentFile(b"dummy", name="dummy.zip"))

    assert (
        PostPublishingCheckReport.objects.filter(
            granularity=PPCReportType.WEEKLY
        ).count()
        == 0
    )

    wr.generate()

    assert (
        PostPublishingCheckReport.objects.filter(
            granularity=PPCReportType.WEEKLY
        ).count()
        == 1
    )


@freeze_time(TEST_DATE)
@patch(mock_path_prefix + "PostPublishingChecksSummaryData.aggregate_daily_reports")
@patch(mock_path_prefix + "WeeklyPPCReportArchiver.to_zip")
def test_created_zip_has_correct_name(
    zip_mock: Mock,
    agg_reports_mock: Mock,
    mockup_reports: FetchedDataType,
    summary_mock: Mock,
) -> None:
    agg_reports_mock.return_value = summary_mock

    wr = WeeklyReport(start_date=date.today())
    wr._fetch_data = Mock(return_value=mockup_reports)
    zip_mock.return_value = ContentFile(b"dummy")

    wr.generate()

    generated_archive = PostPublishingCheckReport.objects.get(
        granularity=PPCReportType.WEEKLY
    )

    feed_id = list(mockup_reports.keys())[0]

    assert generated_archive.file.name == f"Week_30_10_2022_feed_{feed_id}_60.zip"


@freeze_time(TEST_DATE)
@patch(mock_path_prefix + "PostPublishingChecksSummaryData.aggregate_daily_reports")
def test_fetching_data_for_weekly_report(
    agg_reports_mock: Mock, mockup_reports: FetchedDataType
) -> None:
    wr = WeeklyReport(start_date=date.today())
    wr._save_weekly_report = Mock()
    wr._create_zip = Mock()

    wr.generate()

    expected_response = PostPublishingCheckReport.objects.filter(
        created__lte=date.today(),
        created__gt=date.today() - timedelta(weeks=1),
        granularity=PPCReportType.DAILY,
    )

    feed_id = list(mockup_reports.keys())[0]
    assert PostPublishingCheckReport.objects.filter(dataset_id=feed_id).count() > 7
    assert expected_response.count() == 7
    agg_reports_mock.assert_called_once_with(list(expected_response.all()))
