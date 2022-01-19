import pandas as pd
from django.test import TestCase

from transit_odp.naptan.factories import (
    AdminAreaFactory,
    LocalityFactory,
    StopPointFactory,
)
from transit_odp.pipelines.pipelines.naptan_etl.transform import (
    get_existing_data,
    get_new_data,
)
from transit_odp.pipelines.tests.utils import check_frame_equal


class TestNaptanTransform(TestCase):
    def test_get_new_stops(self):
        # Setup
        admin_area1 = AdminAreaFactory(atco_code="1")
        admin_area2 = AdminAreaFactory(atco_code="2")
        locality1 = LocalityFactory(admin_area=admin_area1)
        locality2 = LocalityFactory(admin_area=admin_area2)

        stop1 = StopPointFactory(
            atco_code="123", locality=locality1, admin_area=admin_area1
        )
        stop2 = StopPointFactory(
            atco_code="345", locality=locality2, admin_area=admin_area2
        )
        stops_from_db = pd.DataFrame(
            [{"atco_code": "123", "obj": stop1}, {"atco_code": "345", "obj": stop2}]
        ).set_index("atco_code")
        stops_from_naptan = pd.DataFrame(
            [
                {
                    "atco_code": "123",
                    "naptan_code": "bstpgit",
                    "common_name": "Cassell Road",
                    "indicator": "SW-bound",
                    "street": "Downend Road",
                    "locality_id": "E0035604",
                    "admin_area_id": 9,
                    "latitude": "51.4843326109",
                    "longitude": "-2.51701423067",
                },
                {
                    "atco_code": "345",
                    "naptan_code": "bstpata",
                    "common_name": "The Centre",
                    "indicator": "C4",
                    "street": "Broad Quay",
                    "locality_id": "N0076879",
                    "admin_area_id": 9,
                    "latitude": "51.45306504329",
                    "longitude": "-2.59725334008",
                },
                {
                    "atco_code": "567",
                    "naptan_code": "bstpata",
                    "common_name": "The Centre",
                    "indicator": "C4",
                    "street": "Broad Quay",
                    "locality_id": "N0076879",
                    "admin_area_id": 9,
                    "latitude": "51.45306504329",
                    "longitude": "-2.59725334008",
                },
            ]
        ).set_index("atco_code")

        # Test
        intersection = get_new_data(stops_from_naptan, stops_from_db)

        # Assert
        expected_data = pd.DataFrame(
            [
                {
                    "atco_code": "567",
                    "naptan_code": "bstpata",
                    "common_name": "The Centre",
                    "indicator": "C4",
                    "street": "Broad Quay",
                    "locality_id": "N0076879",
                    "admin_area_id": 9,
                    "latitude": "51.45306504329",
                    "longitude": "-2.59725334008",
                },
            ]
        ).set_index("atco_code")
        self.assertTrue(check_frame_equal(intersection, expected_data))

    def test_get_existing_stops(self):
        # Setup
        admin_area1 = AdminAreaFactory(atco_code="1")
        admin_area2 = AdminAreaFactory(atco_code="2")
        locality1 = LocalityFactory(admin_area=admin_area1)
        locality2 = LocalityFactory(admin_area=admin_area2)

        stop1 = StopPointFactory(
            atco_code="123",
            locality=locality1,
            admin_area=admin_area1,
            common_name="test1",
        )
        stop2 = StopPointFactory(
            atco_code="345",
            locality=locality2,
            admin_area=admin_area2,
            common_name="test2",
        )
        stops_from_db = pd.DataFrame(
            [{"atco_code": "123", "obj": stop1}, {"atco_code": "345", "obj": stop2}]
        ).set_index("atco_code")
        stops_from_naptan = pd.DataFrame(
            [
                {
                    "atco_code": "123",
                    "naptan_code": "bstpgit",
                    "common_name": "Cassell Road",
                    "indicator": "SW-bound",
                    "street": "Downend Road",
                    "locality_id": "E0035604",
                    "admin_area_id": 9,
                    "latitude": "51.4843326109",
                    "longitude": "-2.51701423067",
                },
                {
                    "atco_code": "345",
                    "naptan_code": "bstpata",
                    "common_name": "The Centre",
                    "indicator": "C4",
                    "street": "Broad Quay",
                    "locality_id": "N0076879",
                    "admin_area_id": 9,
                    "latitude": "51.45306504329",
                    "longitude": "-2.59725334008",
                },
                {
                    "atco_code": "567",
                    "naptan_code": "bstpata",
                    "common_name": "The Centre",
                    "indicator": "C4",
                    "street": "Broad Quay",
                    "locality_id": "N0076879",
                    "admin_area_id": 9,
                    "latitude": "51.45306504329",
                    "longitude": "-2.59725334008",
                },
            ]
        ).set_index("atco_code")

        # Test
        intersection = get_existing_data(stops_from_naptan, stops_from_db, "atco_code")

        # Assert
        self.assertEqual(intersection.iloc[0].name, "123")
        self.assertEqual(intersection.iloc[0].common_name, "Cassell Road")

        self.assertEqual(intersection.iloc[1].name, "345")
        self.assertEqual(intersection.iloc[1].common_name, "The Centre")
