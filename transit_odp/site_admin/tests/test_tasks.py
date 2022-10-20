import zipfile
from datetime import date, datetime, timedelta

import pytest
import pytz
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from freezegun import freeze_time

from transit_odp.feedback.factories import FeedbackFactory
from transit_odp.feedback.models import Feedback
from transit_odp.site_admin.factories import (
    APIRequestFactory,
    ResourceRequestCounterFactory,
)
from transit_odp.site_admin.models import (
    APIRequest,
    MetricsArchive,
    ResourceRequestCounter,
)
from transit_odp.site_admin.tasks import (
    DATA_RETENTION_POLICY_MONTHS,
    task_backfill_metrics_archive,
    task_delete_unwanted_data,
)

pytestmark = pytest.mark.django_db


def test_task_backfill_metrics_archive():
    """
    Given 5 APIRequests in Jan and 5 APIRequests in June.
    When running `task_backfill_metrics_archive`.
    Then 5 MetricArchives will be created, one for each month not including June.
    """
    first_date = datetime(2021, 1, 1, tzinfo=pytz.utc)
    APIRequestFactory.create_batch(5, created=first_date)

    last_date = datetime(2021, 6, 1, tzinfo=pytz.utc)
    APIRequestFactory.create_batch(5, created=last_date)

    task_backfill_metrics_archive()

    metrics = MetricsArchive.objects.all()

    assert metrics.count() == 5
    assert metrics.order_by("start").last().start == datetime(2021, 5, 1).date()


@pytest.mark.parametrize(
    "test_dates, expected_dates",
    [
        (
            [
                # Timezone British Summer Time (BST)
                timezone.datetime(2022, 6, 1),
                timezone.datetime(2022, 6, 30),
                timezone.datetime(2022, 6, 30, 23, 59),
                timezone.datetime(2022, 6, 29),
                timezone.datetime(2022, 7, 1, 4),
                timezone.datetime(2022, 7, 1),
                timezone.datetime(2022, 7, 2),
                timezone.datetime(2022, 7, 1, 0, 30),
            ],
            ["2022-06-01"] * 2 + ["2022-06-29"] * 2 + ["2022-06-30"] * 4,
        ),
        (
            [
                # Timezone Greenwich Mean Time (GMT)
                datetime(2022, 12, 1, tzinfo=pytz.utc),
                datetime(2022, 12, 31, tzinfo=pytz.utc),
                datetime(2022, 12, 31, 23, 59, tzinfo=pytz.utc),
                datetime(2022, 12, 30, tzinfo=pytz.utc),
                datetime(2023, 1, 1, 4, tzinfo=pytz.utc),
                datetime(2023, 1, 1, tzinfo=pytz.utc),
                datetime(2023, 1, 2, tzinfo=pytz.utc),
                datetime(2023, 1, 1, 0, 30, tzinfo=pytz.utc),
            ],
            ["2022-12-01"] * 2 + ["2022-12-30"] * 2 + ["2022-12-31"] * 4,
        ),
    ],
)
def test_task_backfill_is_timezone_secure(
    test_dates: list[datetime], expected_dates: list[str]
) -> None:
    """
    NOTE: APIRequest.created is always saved/fetched in UTC format.

    Given dates from turn of the month should be correctly fetched
    and displayed in first column of generated CSV file.
    First column should contain only dates from one month.

    Solves bug: https://itoworld.atlassian.net/browse/BODP-5526
    """

    for test_date in test_dates:
        APIRequestFactory.create_batch(2, created=test_date)

    task_backfill_metrics_archive()

    metrics = MetricsArchive.objects.all()

    month = test_dates[0].month
    archive = next(metric for metric in metrics if metric.start.month == month).archive

    generated_dates = []
    with zipfile.ZipFile(archive, "r") as z:
        with z.open("dailyconsumerbreakdown.csv") as csvfile:
            csvfile.readline()  # Pops headers
            for line in csvfile.readlines():
                row = str(line, "utf-8").split(",")
                generated_dates.append(row[0])

    assert generated_dates == expected_dates


def test_task_backfill_sorts_entries_by_date():
    """
    Final Dataframe is generated by merging APIRequest dataframe
    and ResourceRequestCounter dataframe.
    It might happen the dates differ and outer join produces incorrectly sorted
    dataframe.
    """
    test_dates = [
        timezone.datetime(2022, 6, 15),
        timezone.datetime(2022, 6, 28),
    ]

    expected_dates = ["2022-06-15"] * 2 + ["2022-06-24"] + ["2022-06-28"] * 2

    for test_date in test_dates:
        APIRequestFactory.create_batch(2, created=test_date)

    ResourceRequestCounterFactory(date=timezone.datetime(2022, 6, 24))

    task_backfill_metrics_archive()

    metrics = MetricsArchive.objects.all()

    archive_june = next(metric for metric in metrics if metric.start.month == 6).archive

    generated_dates = []
    with zipfile.ZipFile(archive_june, "r") as z:
        with z.open("dailyconsumerbreakdown.csv") as csvfile:
            csvfile.readline()  # Pops headers
            for line in csvfile.readlines():
                row = str(line, "utf-8").split(",")
                generated_dates.append(row[0])

    assert generated_dates == expected_dates


def test_task_delete_unwanted_data():
    now = timezone.now()
    the_past = now - relativedelta(months=DATA_RETENTION_POLICY_MONTHS, days=1)
    APIRequestFactory()
    ResourceRequestCounterFactory()
    ResourceRequestCounterFactory(date=the_past)
    APIRequestFactory(created=the_past)

    task_delete_unwanted_data()
    assert ResourceRequestCounter.objects.count() == 1
    assert APIRequest.objects.count() == 1


def test_delete_data_from_near_to_policy():
    now = timezone.now()
    policy = relativedelta(months=DATA_RETENTION_POLICY_MONTHS)
    boundary = now - policy
    inside_boundary = boundary + relativedelta(days=1)
    outside_boundary = boundary - relativedelta(days=1)
    APIRequestFactory(created=inside_boundary)
    APIRequestFactory(created=boundary)
    deleted = APIRequestFactory(created=outside_boundary)

    task_delete_unwanted_data()
    assert APIRequest.objects.count() == 1
    assert not APIRequest.objects.filter(id=deleted.id).exists()


@freeze_time("2022-01-02")
def test_delete_website_feedback():
    base_date = date(2020, 1, 1)
    FeedbackFactory(date=base_date)
    FeedbackFactory(date=base_date + timedelta(days=1))
    fb = FeedbackFactory(date=base_date + timedelta(days=2))

    task_delete_unwanted_data()
    assert Feedback.objects.count() == 1
    assert Feedback.objects.first() == fb
