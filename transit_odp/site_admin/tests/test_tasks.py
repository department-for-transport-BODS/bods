from datetime import datetime

import pytest
import pytz

from transit_odp.site_admin.factories import APIRequestFactory
from transit_odp.site_admin.models import MetricsArchive
from transit_odp.site_admin.tasks import task_backfill_metrics_archive

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
