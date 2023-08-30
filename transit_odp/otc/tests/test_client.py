from datetime import datetime
from unittest.mock import patch

from freezegun import freeze_time

from transit_odp.otc.client import OTCAPIClient
from transit_odp.otc.client.enums import RegistrationStatusEnum


@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
def test_expected_number_of_registrations_returned(otc_data_from_filename_status):
    client = OTCAPIClient()
    registrations = list(client.get_latest_variations_by_reg_status("Registered"))
    assert len(registrations) == 500


@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
def test_get_variations_by_registration_code_desc_orders(
    otc_data_from_filename_truncated,
):
    client = OTCAPIClient()
    registrations = client.get_variations_by_registration_code_desc("PB0000092/132")
    assert registrations[0].variation_number == 51
    assert registrations[0].registration_status == RegistrationStatusEnum.EXPIRED.value


@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
@freeze_time("2022-11-09")
def test_get_variations_since(
    otc_data_from_filename_date,
):
    regs_per_day = (137, 12, 2, 147, 210)
    client = OTCAPIClient()
    registrations = client.get_latest_variations_since(datetime(2022, 11, 4))
    assert len(registrations) == sum(regs_per_day)


@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
@freeze_time("2022-11-09")
def test_get_variations_since_with_no_content(
    date_data_with_no_content,
):
    regs_per_day = (137, 12, 0, 147, 210)
    client = OTCAPIClient()
    registrations = client.get_latest_variations_since(datetime(2022, 11, 4))
    assert len(registrations) == sum(regs_per_day)


@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
@freeze_time("2022-11-09")
def test_get_no_content(
    date_data_with_no_content,
):
    client = OTCAPIClient()
    response = client._make_request(
        page=1, lastModifiedOn="2022-11-06", latestVariation=True
    )
    assert response.bus_search == []
    assert response.page.total_pages == 1
    assert response.page.current == 1
    assert response.page.total_count == 0
