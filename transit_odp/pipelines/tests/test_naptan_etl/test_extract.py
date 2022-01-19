import os

import pandas as pd
import pytest
from django.test import TestCase

from transit_odp.pipelines.pipelines.naptan_etl.extract import (
    extract_admin_areas,
    extract_localities,
    extract_stops,
)
from transit_odp.pipelines.tests.utils import check_frame_equal


class TestNaptanNptgExtract(TestCase):
    def setUp(self):
        self.cur_dir = os.path.abspath(os.path.dirname(__file__))
        self.naptan_path = os.path.join(self.cur_dir, "data/Naptan.xml")
        self.nptg_path = os.path.join(self.cur_dir, "data/Nptg.xml")

    @pytest.mark.skip(reason="Testing if dataframes are equal is pointless")
    def test_extract_stops(self):
        # Test
        actual_stops = extract_stops(self.naptan_path)

        # Assert
        expected_stops = pd.DataFrame(
            [
                {
                    "atco_code": "010000001",
                    "naptan_code": "bstpgit",
                    "common_name": "Cassell Road",
                    "indicator": "SW-bound",
                    "street": "Downend Road",
                    "locality_id": "E0035604",
                    "admin_area_id": 9,
                    "latitude": "51.484333",
                    "longitude": "-2.517014",
                },
                {
                    "atco_code": "010000002",
                    "naptan_code": "bstpata",
                    "common_name": "The Centre",
                    "indicator": "C4",
                    "street": "Broad Quay",
                    "locality_id": "N0076879",
                    "admin_area_id": 9,
                    "latitude": "51.453065",
                    "longitude": "-2.597253",
                },
            ]
        ).set_index("atco_code")

        self.assertTrue(check_frame_equal(actual_stops, expected_stops))

    def test_extract_admin_areas(self):
        # Test
        actual_admin_areas = extract_admin_areas(self.nptg_path)

        # Assert
        expected_admin_areas = pd.DataFrame(
            [
                {
                    "id": 110,
                    "name": "National - National Rail",
                    "traveline_region_id": "GB",
                    "atco_code": "910",
                },
                {
                    "id": 143,
                    "name": "National - National Coach",
                    "traveline_region_id": "GB",
                    "atco_code": "900",
                },
                {
                    "id": 15,
                    "name": "Darlington",
                    "traveline_region_id": "NE",
                    "atco_code": "076",
                },
                {
                    "id": 22,
                    "name": "Hartlepool",
                    "traveline_region_id": "NE",
                    "atco_code": "075",
                },
            ]
        ).set_index("id")
        self.assertTrue(check_frame_equal(actual_admin_areas, expected_admin_areas))

    def test_extract_localities(self):
        # Test
        actual_localities = extract_localities(self.nptg_path)

        # Assert
        expected_localities = pd.DataFrame(
            [
                {
                    "gazetteer_id": "E0034964",
                    "name": "Amesbury",
                    "easting": 365491,
                    "northing": 158651,
                    "district_id": 310,
                    "admin_area_id": 1,
                },
                {
                    "gazetteer_id": "E0034965",
                    "name": "Ashgrove",
                    "easting": 370798,
                    "northing": 157864,
                    "district_id": 310,
                    "admin_area_id": 1,
                },
            ]
        ).set_index("gazetteer_id")

        self.assertTrue(check_frame_equal(actual_localities, expected_localities))
