from datetime import datetime

import pytest
import pytz
from dateutil.relativedelta import relativedelta

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


def test_task_delete_unwanted_data():
    now = datetime.now()
    the_past = now - relativedelta(months=DATA_RETENTION_POLICY_MONTHS, days=1)
    APIRequestFactory()
    ResourceRequestCounterFactory()
    ResourceRequestCounterFactory(date=the_past)
    APIRequestFactory(created=the_past)

    task_delete_unwanted_data()
    assert ResourceRequestCounter.objects.count() == 1
    assert APIRequest.objects.count() == 1


def test_delete_data_from_far_away_from_policy():
    now = datetime.now()
    policy = relativedelta(months=DATA_RETENTION_POLICY_MONTHS)
    old = now - policy
    really_old = old - policy
    APIRequestFactory()
    APIRequestFactory(created=old)
    deleted = APIRequestFactory(created=really_old)

    task_delete_unwanted_data()
    assert APIRequest.objects.count() == 2
    assert not APIRequest.objects.filter(id=deleted.id).exists()


def test_delete_data_from_nearer_to_policy():
    now = datetime.now()
    policy = relativedelta(months=DATA_RETENTION_POLICY_MONTHS)
    old = now - policy
    older = old - relativedelta(days=3)
    APIRequestFactory()
    APIRequestFactory(created=old)
    deleted = APIRequestFactory(created=older)

    task_delete_unwanted_data()
    assert APIRequest.objects.count() == 2
    assert not APIRequest.objects.filter(id=deleted.id).exists()


def test_delete_data_from_near_to_policy():
    now = datetime.now()
    policy = relativedelta(months=DATA_RETENTION_POLICY_MONTHS)
    boundary = now - policy
    inside_boundary = boundary + relativedelta(days=1)
    outside_boundary = boundary - relativedelta(days=1)
    APIRequestFactory(created=inside_boundary)
    APIRequestFactory(created=boundary)
    deleted = APIRequestFactory(created=outside_boundary)

    task_delete_unwanted_data()
    assert APIRequest.objects.count() == 2
    assert not APIRequest.objects.filter(id=deleted.id).exists()
