import pytest

from transit_odp.otc.models import Licence, Operator, Service
from transit_odp.otc.tasks import task_refresh_otc_data
from transit_odp.otc.tests.conftest import CSV_DATA

pytestmark = pytest.mark.django_db


def test_task_runs_successfully(otc_urls):
    task_refresh_otc_data()

    assert Operator.objects.count() == 908
    assert Service.objects.count() == sum(row[3] for row in CSV_DATA)
    assert Licence.objects.count() == sum(row[4] for row in CSV_DATA)


def test_task_handles_a_bad_request(bad_otc_urls):
    task_refresh_otc_data()
