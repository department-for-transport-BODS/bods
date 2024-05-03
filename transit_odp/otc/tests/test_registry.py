from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from transit_odp.otc.client.enums import RegistrationStatusEnum
from transit_odp.otc.factories import (
    LicenceFactory,
    OperatorFactory,
    RegistrationFactory,
    ServiceFactory,
    flatten_data,
)
from transit_odp.otc.registry import Registry

pytestmark = pytest.mark.django_db
CLIENT = "transit_odp.otc.client.otc_client.OTCAPIClient"


def create_backstory_for_registration(registration, good_status):
    variations = [registration]

    new = registration.copy()
    new.variation_number -= 1
    variations.append(new)

    new = new.copy()
    new.variation_number -= 1
    new.registration_status = RegistrationStatusEnum.WITHDRAWN.value
    variations.append(new)

    new = new.copy()
    new.variation_number -= 1
    new.registration_status = good_status
    new.service_type_description = "Normal Stopping"
    variations.append(new)

    new = new.copy()
    new.service_type_description = "School Service"
    variations.append(new)

    new = new.copy()
    new.trading_name = "not important"
    new.variation_number -= 1
    variations.append(new)

    for _ in range(5):
        new = new.copy()
        new.registration_status = RegistrationStatusEnum.REGISTERED.value
        new.variation_number -= 1
        variations.append(new)

    return sorted(variations, key=lambda obj: obj.variation_number, reverse=True)


# @patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
# @patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
# def test_registry_normalises_data(otc_data_from_filename_status):
#     registry = Registry()
#     registry.add_all_latest_registered_variations()

#     assert len(registry.operators) == 12
#     assert len(registry.licences) == 12
#     assert len(registry.services) == 406


@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
def test_registry_returns_highest_non_expired_variation(
    otc_data_from_filename_truncated,
):
    registry = Registry()
    service = registry.get_latest_variations_by_id("PB0000092/132")
    for variation in service:
        assert variation.variation_number == 50
        assert variation.registration_status == RegistrationStatusEnum.REGISTERED.value

@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
def test_registry_returns_expired_variation_if_veration_number_zero(
    otc_data_from_filename_truncated,
):
    registry = Registry()
    service = registry.get_latest_variations_by_id("PC2021320/53")
    print(service)
    for variation in service:
        assert variation.variation_number == 0
        assert variation.registration_status == RegistrationStatusEnum.EXPIRED.value


@freeze_time("25/12/2022")
@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
@patch(f"{CLIENT}.get_variations_by_registration_code_desc")
@patch(f"{CLIENT}.get_latest_variations_since")
def test_get_latest_variations_since_returns_all_service_types(mock_all, mock_detail):
    now = timezone.now()
    one_day_ago = now - timedelta(days=1)
    registrations = RegistrationFactory.create_batch(5)
    refetch1, refetch2 = RegistrationFactory.create_batch(
        2, registration_status=RegistrationStatusEnum.EXPIRED.value
    )
    registrations = registrations + [refetch1, refetch2]

    mock_all.return_value = registrations
    mock_detail.side_effect = [
        create_backstory_for_registration(
            refetch1, RegistrationStatusEnum.REGISTERED.value
        ),
        create_backstory_for_registration(
            refetch2, RegistrationStatusEnum.SURRENDERED.value
        ),
    ]
    registry = Registry()
    registry.get_variations_since(one_day_ago, [])

    assert len(registry.services) == 5 + 2 + 2
    service = registry.get_service_by_key(
        refetch1.registration_number, "Normal Stopping"
    )
    assert service.registration_status == RegistrationStatusEnum.REGISTERED.value
    service = registry.get_service_by_key(
        refetch1.registration_number, "School Service"
    )
    assert service.registration_status == RegistrationStatusEnum.REGISTERED.value

    service = registry.get_service_by_key(
        refetch2.registration_number, "Normal Stopping"
    )
    assert service is not None
    service = registry.get_service_by_key(
        refetch2.registration_number, "School Service"
    )
    assert service is not None


@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
@patch(f"{CLIENT}.get_latest_variations_by_reg_status")
def test_last_modified_is_defined_and_not_none(otc_data_from_filename_status):
    registry = Registry()
    registry.add_all_latest_registered_variations()
    for service in registry.services:
        assert service.last_modified is not None


# @patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
# @patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
# def test_number_of_registered_services_expected(otc_data_from_filename_status):
#     registry = Registry()
#     registry.add_all_latest_registered_variations()

#     assert len(registry.services) == 406


@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
def test_unique_number_of_further_lookup_ids_expected(otc_data_from_filename_status):
    registry = Registry()
    lookup_ids = registry.get_further_lookup_ids()

    assert len(lookup_ids) == 998


@patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
@patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
def test_can_revert_to_earlier_verisons(otc_data_from_filename_truncated):
    registry = Registry()
    registry.add_all_older_registered_variations()

    assert len(registry.services) == 16


# @patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
# @patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
# @freeze_time("2022-11-08")
# def test_can_get_variations_since_drop_bad_data(otc_date_data_truncated):
#     registry = Registry()
#     registry.get_variations_since(datetime(2022, 11, 5))

#     assert len(registry.services) == 11


# @patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
# @patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
# @freeze_time("2022-11-08")
# def test_can_get_variations_since_can_skip_no_content(
#     otc_date_data_truncated_no_content,
# ):
#     registry = Registry()
#     registry.get_variations_since(datetime(2022, 11, 5))

#     assert len(registry.services) == 10


# @freeze_time("2022-11-08")
# @patch("django.conf.settings.OTC_API_KEY", "dummy_otc_api_key")
# @patch("transit_odp.otc.client.OTCAuthenticator.token", "dummy_token")
# def test_update_keeps_latest_variations(mocker):
#     operator = OperatorFactory()
#     l1 = LicenceFactory(number="LD0000007")
#     old = ServiceFactory(
#         operator=operator,
#         licence=l1,
#         registration_code=101,
#         service_type_description="school",
#         registration_status=RegistrationStatusEnum.REGISTERED.value,
#         variation_number=9,
#         public_text="old text",
#     )
#     new = ServiceFactory(
#         operator=operator,
#         licence=l1,
#         registration_code=101,
#         service_type_description="school",
#         registration_status=RegistrationStatusEnum.REGISTERED.value,
#         variation_number=11,
#         public_text="new text",
#     )
#     mock = Mock()
#     mock.get_latest_variations_since.return_value = flatten_data([old, new])
#     mocker.patch("transit_odp.otc.registry.OTCAPIClient", return_value=mock)
#     registry = Registry()
#     registry.get_variations_since(datetime(2022, 11, 6), [])
#     assert registry.services[0].variation_number == 11
#     assert registry.services[0].public_text == "new text"
