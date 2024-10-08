import pandas as pd
from django.test import TestCase
from django.contrib.gis.geos import Point

from transit_odp.naptan.factories import (
    AdminAreaFactory,
    LocalityFactory,
    StopPointFactory,
)
from transit_odp.pipelines.pipelines.naptan_etl.transform import (
    get_existing_data,
    get_new_data,
    get_stops_to_update,
    get_admin_areas_to_update,
    get_localities_to_update,
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

    def test_get_stops_to_update(self):
        admin_area1 = AdminAreaFactory(atco_code="1")
        admin_area2 = AdminAreaFactory(atco_code="2")
        locality1 = LocalityFactory(admin_area=admin_area1, gazetteer_id="E0035604")
        locality2 = LocalityFactory(admin_area=admin_area2, gazetteer_id="N0076879")

        stop1 = StopPointFactory(
            atco_code="123",
            locality=locality1,
            admin_area=admin_area1,
            naptan_code="bstpgit",
            common_name="Cassell Road",
            indicator="SW-bound",
            street="Downend Road",
            location=Point(float(51.4843326109), float(-2.51701423067), srid=4326),
        )
        stop2 = StopPointFactory(
            atco_code="345",
            locality=locality2,
            admin_area=admin_area2,
            naptan_code="bst",
            common_name="The Centre",
            indicator="C4",
            street="Broad Quay",
            location=Point(float(51.4843326109), float(-2.51701423067), srid=4326),
        )
        stop3 = StopPointFactory(
            atco_code="567",
            naptan_code="bstpata",
            common_name="The Centre",
            locality=locality2,
            admin_area=admin_area2,
            indicator="C4",
            street="Broad Quay",
            location=Point(float(51.4843326109), float(-2.51701423067), srid=4326),
        )
        stops_from_db = pd.DataFrame(
            [
                {"atco_code": "123", "obj": stop1},
                {"atco_code": "345", "obj": stop2},
                {"atco_code": "567", "obj": stop3},
            ]
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
                    "location": Point(
                        float(51.4843326109), float(-2.51701423067), srid=4326
                    ),
                },
                {
                    "atco_code": "345",
                    "naptan_code": "bstpata",
                    "common_name": "The Centre",
                    "indicator": "C4",
                    "street": "Broad Quay",
                    "locality_id": "N0076879",
                    "location": Point(
                        float(51.4843326109), float(-2.51701423067), srid=4326
                    ),
                },
                {
                    "atco_code": "567",
                    "naptan_code": "bstpata",
                    "common_name": "The Centre",
                    "indicator": "C4",
                    "street": "Broad Quay",
                    "locality_id": "N0076879",
                    "location": Point(
                        float(51.4843326109), float(-2.51701423067), srid=4326
                    ),
                },
            ]
        ).set_index("atco_code")

        intersection = get_existing_data(stops_from_naptan, stops_from_db, "atco_code")
        stop_to_update = get_stops_to_update(intersection)
        self.assertEqual(len(stop_to_update), 1)
        self.assertNotEqual(
            stop_to_update.iloc[0].obj.naptan_code, stop_to_update.iloc[0].naptan_code
        )

    def test_get_admin_areas_to_update(self):
        admin_area1 = AdminAreaFactory(
            atco_code="250", name="Lancashire", traveline_region_id="NW"
        )
        admin_area2 = AdminAreaFactory(
            atco_code="113", name="Angus", traveline_region_id="S"
        )
        admin_area3 = AdminAreaFactory(
            atco_code="114", name="Argyll & Bute", traveline_region_id="S"
        )

        adminareas_from_db = pd.DataFrame(
            [
                {"id": 1, "obj": admin_area1},
                {"id": 2, "obj": admin_area2},
                {"id": 3, "obj": admin_area3},
            ]
        ).set_index("id")

        adminareas_from_naptan = pd.DataFrame(
            [
                {
                    "id": 1,
                    "atco_code": "250",
                    "name": "Lancashire",
                    "traveline_region_id": "NW",
                },
                {
                    "id": 2,
                    "atco_code": "251",
                    "name": "Lancashire",
                    "traveline_region_id": "S",
                },
                {
                    "id": 3,
                    "atco_code": "114",
                    "name": "Argyll & Bute",
                    "traveline_region_id": "S",
                },
            ]
        ).set_index("atco_code")

        intersection = get_existing_data(
            adminareas_from_naptan, adminareas_from_db, "id"
        )
        admin_areas_to_update = get_admin_areas_to_update(intersection)
        self.assertEqual(len(admin_areas_to_update), 1)
        self.assertNotEqual(
            admin_areas_to_update.iloc[0].obj.name, admin_areas_to_update.iloc[0].name
        )

    def test_get_localities_to_update(self):
        admin_area1 = AdminAreaFactory(
            atco_code="250", name="Lancashire", traveline_region_id="NW"
        )
        admin_area2 = AdminAreaFactory(
            atco_code="113", name="Angus", traveline_region_id="S"
        )
        admin_area3 = AdminAreaFactory(
            atco_code="Argyll & Bute", name="114", traveline_region_id="S"
        )

        locality1 = LocalityFactory(
            admin_area=admin_area1,
            gazetteer_id="E0035604",
            name="Bailbrook",
            easting=376748,
            northing=167119,
        )
        locality2 = LocalityFactory(
            admin_area=admin_area2,
            gazetteer_id="E0034970",
            name="Barrow Vale",
            easting=364747,
            northing=160235,
        )
        locality3 = LocalityFactory(
            admin_area=admin_area3,
            gazetteer_id="E0034972",
            name="Beacon Hill",
            easting=375140,
            northing=166178,
        )

        localities_from_db = pd.DataFrame(
            [
                {"gazetteer_id": "E0035604", "obj": locality1},
                {"gazetteer_id": "E0034970", "obj": locality2},
                {"gazetteer_id": "E0034972", "obj": locality3},
            ]
        ).set_index("gazetteer_id")

        localities_from_naptan = pd.DataFrame(
            [
                {
                    "gazetteer_id": "E0035604",
                    "name": "Barrow Vale",
                    "easting": 376748,
                    "northing": 167119,
                },
                {
                    "gazetteer_id": "E0034970",
                    "name": "Barrow Vale",
                    "easting": 364747,
                    "northing": 160235,
                },
                {
                    "gazetteer_id": "E0034972",
                    "name": "Beacon Hill",
                    "easting": 375140,
                    "northing": 166178,
                },
            ]
        ).set_index("gazetteer_id")

        intersection = get_existing_data(
            localities_from_naptan, localities_from_db, "gazetteer_id"
        )
        localities_to_update = get_localities_to_update(intersection)
        self.assertEqual(len(localities_to_update), 1)
        self.assertNotEqual(
            localities_to_update.iloc[0].obj.name, localities_to_update.iloc[0].name
        )
