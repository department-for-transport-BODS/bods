from datetime import timedelta
from unittest.mock import patch

import pytest
import requests_mock
from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time
from requests import HTTPError
from tenacity import RetryError

from transit_odp.otc.factories import ServiceModelFactory
from transit_odp.otc.models import Licence, Operator, Service
from transit_odp.otc.tasks import task_get_all_otc_data, task_refresh_otc_data
from transit_odp.otc.tests.conftest import TestableOTCAPIClient

pytestmark = pytest.mark.django_db


@patch("transit_odp.otc.registry.OTCAPIClient", TestableOTCAPIClient)
@requests_mock.Mocker(kw="m")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@freeze_time("09/11/2022")
def test_task_handles_a_bad_request(**kwargs):
    m = kwargs["m"]
    now = timezone.now()
    last_updated = now - timedelta(days=1)
    ServiceModelFactory(last_modified=last_updated)
    qp = "limit=100&page=1&lastModifiedOn=2022-09-10&latestVariation=True"
    m.get(
        f"{settings.OTC_API_URL}?{qp}",
        complete_qs=True,
        status_code=404,
    )
    with pytest.raises(RetryError) as e:
        task_refresh_otc_data()
    assert isinstance(e.value.args[0]._exception, HTTPError)


# @patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
# @patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
# def test_task_with_otc_data(otc_data_from_filename_truncated):
#     task_get_all_otc_data()
#     assert Operator.objects.count() == 13
#     assert Service.objects.count() == 21
#     assert Licence.objects.count() == 13
