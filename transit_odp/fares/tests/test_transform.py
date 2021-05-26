import pytest
from dateutil.parser import parse as parse_datetime_str

from transit_odp.fares.transform import NeTExDocumentsTransformer
from transit_odp.naptan.factories import StopPointFactory

pytestmark = pytest.mark.django_db

TEST_DATA = [
    (
        {
            "schema_version": "1.1",
            "num_of_lines": 1,
            "num_of_fare_zones": 8,
            "num_of_fare_products": 1,
            "num_of_sales_offer_packages": 1,
            "num_of_user_profiles": 4,
            "valid_from": parse_datetime_str("2020-06-22T13:51:43.044Z"),
            "valid_to": parse_datetime_str("2119-06-22T13:51:43.044Z"),
            "stop_point_refs": [
                "atco:3290YYA00077",
                "atco:3290YYA00928",
                "atco:3290YYA00359",
                "atco:3290YYA03623",
                "atco:3290YYA01607",
                "atco:3290YYA01666",
                "atco:3290YYA01609",
                "atco:3290YYA01611",
                "atco:3290YYA00193",
                "atco:3290YYA00192",
                "atco:3290YYA00149",
                "atco:3290YYA00136",
                "atco:3290YYA00103",
                "atco:3290YYA00100",
                "atco:3290YYA00922",
            ],
        },
        {
            "schema_version": "1.1",
            "num_of_lines": 1,
            "num_of_fare_zones": 8,
            "num_of_fare_products": 1,
            "num_of_sales_offer_packages": 1,
            "num_of_user_profiles": 4,
            "valid_from": parse_datetime_str("2020-06-22T13:51:43.044Z"),
            "valid_to": parse_datetime_str("2119-06-22T13:51:43.044Z"),
            "naptan_stop_ids": [1, 2],
        },
    ),
    (
        {
            "schema_version": "1.1",
            "num_of_lines": 1,
            "num_of_fare_zones": 8,
            "num_of_fare_products": 1,
            "num_of_sales_offer_packages": 1,
            "num_of_user_profiles": 4,
            "valid_from": parse_datetime_str("2020-06-22T13:51:43.044Z"),
            "valid_to": parse_datetime_str("2119-06-22T13:51:43.044Z"),
            "stop_point_refs": [
                "atco:3290YYA00077",
                "atco:3290YYA00928",
                "naptan:2500B0271",
                "naptan:2500IMG88",
                "naptStop:123456",
                "naptStop:",
                "atco:",
            ],
        },
        {
            "schema_version": "1.1",
            "num_of_lines": 1,
            "num_of_fare_zones": 8,
            "num_of_fare_products": 1,
            "num_of_sales_offer_packages": 1,
            "num_of_user_profiles": 4,
            "valid_from": parse_datetime_str("2020-06-22T13:51:43.044Z"),
            "valid_to": parse_datetime_str("2119-06-22T13:51:43.044Z"),
            "naptan_stop_ids": [3, 4, 1, 2, 5],
        },
    ),
]


@pytest.mark.parametrize("input,expected", TEST_DATA)
def test_transform_stop_point_refs(input, expected):
    StopPointFactory.create(id=1, atco_code="3290YYA00077")
    StopPointFactory.create(id=2, atco_code="3290YYA00928")
    StopPointFactory.create(id=3, atco_code="2500B0271")
    StopPointFactory.create(id=4, atco_code="2500IMG88")
    StopPointFactory.create(id=5, atco_code="7890", naptan_code="123456")
    transformer = NeTExDocumentsTransformer(input)
    actual = transformer.transform_data()
    assert actual == expected
