from unittest.mock import patch

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
