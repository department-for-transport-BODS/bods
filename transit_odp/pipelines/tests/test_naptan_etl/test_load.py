import pandas as pd
from django.contrib.gis.geos import Point
from django.test import TestCase

from transit_odp.naptan.factories import (
    AdminAreaFactory,
    DistrictFactory,
    LocalityFactory,
    StopPointFactory,
)
from transit_odp.naptan.models import AdminArea, Locality, StopPoint
from transit_odp.pipelines.pipelines.naptan_etl.load import (
    load_existing_admin_areas,
    load_existing_localities,
    load_existing_stops,
    load_new_admin_areas,
    load_new_localities,
    load_new_stops,
)


class TestNaptanLoad(TestCase):
    def test_load_new_stops(self):
        # Setup
        AdminAreaFactory(id=9, atco_code="123")
        LocalityFactory(gazetteer_id="E0035604")
        new_stops = pd.DataFrame(
            [
                {
                    "atco_code": "010000001",
                    "naptan_code": "bstpgit",
                    "common_name": "Cassell Road",
                    "indicator": "SW-bound",
                    "street": "Downend Road",
                    "locality_id": "E0035604",
                    "admin_area_id": 9,
                    "latitude": "51.4843326109",
                    "longitude": "-2.51701423067",
                    "stop_areas": ["stop1"],
                },
            ]
        ).set_index("atco_code")

        # Test
        load_new_stops(new_stops)

        # Assert
        created_stop = StopPoint.objects.all()[0]

        self.assertEqual(len(StopPoint.objects.all()), 1)
        self.assertEqual(created_stop.naptan_code, "bstpgit")
        self.assertEqual(created_stop.atco_code, "010000001")
        self.assertEqual(created_stop.common_name, "Cassell Road")
        self.assertEqual(created_stop.indicator, "SW-bound")
        self.assertEqual(created_stop.street, "Downend Road")
        self.assertEqual(created_stop.locality_id, "E0035604")
        self.assertEqual(created_stop.admin_area_id, 9)
        self.assertEqual(created_stop.stop_areas, ["stop1"])
        self.assertEqual(
            created_stop.location,
            Point(x=float("-2.51701423067"), y=float("51.4843326109"), srid=4326),
        )

    def test_update_existing_stops(self):
        # Setup
        admin_area = AdminAreaFactory(id=9, atco_code="123")
        locality = LocalityFactory(gazetteer_id="E0035604")
        stop = StopPointFactory(
            admin_area=admin_area,
            locality=locality,
            atco_code="010000001",
            common_name="TestName1",
            stop_areas=[],
        )
        existing_stops = pd.DataFrame(
            [
                {
                    "atco_code": "010000001",
                    "naptan_code": "bstpgit",
                    "common_name": "Cassell Road",
                    "indicator": "SW-bound",
                    "street": "Downend Road",
                    "locality_id": "E0035604",
                    "admin_area_id": 9,
                    "latitude": "51.4843326109",
                    "longitude": "-2.51701423067",
                    "stop_areas": ["stop1"],
                    "obj": stop,
                },
            ]
        ).set_index("atco_code")

        # Test
        load_existing_stops(existing_stops)

        # Assert
        updated_stop = StopPoint.objects.all()[0]

        self.assertEqual(len(StopPoint.objects.all()), 1)
        self.assertEqual(updated_stop.naptan_code, "bstpgit")
        self.assertEqual(updated_stop.atco_code, "010000001")
        self.assertEqual(updated_stop.common_name, "Cassell Road")
        self.assertEqual(updated_stop.indicator, "SW-bound")
        self.assertEqual(updated_stop.street, "Downend Road")
        self.assertEqual(updated_stop.locality_id, "E0035604")
        self.assertEqual(updated_stop.admin_area_id, 9)
        self.assertEqual(updated_stop.stop_areas, ["stop1"])
        self.assertEqual(
            updated_stop.location,
            Point(x=float("-2.51701423067"), y=float("51.4843326109"), srid=4326),
        )

    def test_load_new_admin_areas(self):
        # Setup
        new_admin_areas = pd.DataFrame(
            [
                {
                    "id": 1,
                    "name": "AdminArea1",
                    "traveline_region_id": "GB",
                    "atco_code": "123",
                },
            ]
        ).set_index("id")

        # Test
        load_new_admin_areas(new_admin_areas)

        # Assert
        created_admin_area = AdminArea.objects.all()[0]

        self.assertEqual(len(AdminArea.objects.all()), 1)
        self.assertEqual(created_admin_area.id, 1)
        self.assertEqual(created_admin_area.name, "AdminArea1")
        self.assertEqual(created_admin_area.traveline_region_id, "GB")
        self.assertEqual(created_admin_area.atco_code, "123")

    def test_update_existing_admin_areas(self):
        # Setup
        admin_area = AdminAreaFactory(
            id=1, name="TestAdminArea", traveline_region_id="GB", atco_code="123"
        )
        existing_admin_areas = pd.DataFrame(
            [
                {
                    "id": 1,
                    "name": "AdminArea1",
                    "traveline_region_id": "NW",
                    "atco_code": "234",
                    "obj": admin_area,
                },
            ]
        ).set_index("id")

        # Test
        load_existing_admin_areas(existing_admin_areas)

        # Assert
        updated_admin_area = AdminArea.objects.all()[0]

        self.assertEqual(len(AdminArea.objects.all()), 1)
        self.assertEqual(updated_admin_area.id, 1)
        self.assertEqual(updated_admin_area.name, "AdminArea1")
        self.assertEqual(updated_admin_area.traveline_region_id, "NW")
        self.assertEqual(updated_admin_area.atco_code, "234")

    def test_load_new_localities(self):
        # Setup
        AdminAreaFactory(id=9, atco_code="123")
        DistrictFactory(id=10)
        new_localities = pd.DataFrame(
            [
                {
                    "gazetteer_id": "N1",
                    "name": "Locality1",
                    "easting": 12345,
                    "northing": 34567,
                    "admin_area_id": 9,
                    "district_id": 10,
                },
            ]
        ).set_index("gazetteer_id")

        # Test
        load_new_localities(new_localities)

        # Assert
        created_locality = Locality.objects.all()[0]

        self.assertEqual(len(Locality.objects.all()), 1)
        self.assertEqual(created_locality.gazetteer_id, "N1")
        self.assertEqual(created_locality.name, "Locality1")
        self.assertEqual(created_locality.easting, 12345)
        self.assertEqual(created_locality.northing, 34567)
        self.assertEqual(created_locality.admin_area_id, 9)
        # self.assertEqual(created_locality.district_id, 10)

    def test_update_existing_localities(self):
        # Setup
        admin_area = AdminAreaFactory(id=19, atco_code="123")
        district = DistrictFactory(id=20)
        AdminAreaFactory(id=9)
        DistrictFactory(id=10)
        locality = LocalityFactory(
            gazetteer_id="N1",
            name="TestLocality",
            admin_area=admin_area,
            district=district,
            easting=1,
            northing=2,
        )
        existing_localities = pd.DataFrame(
            [
                {
                    "gazetteer_id": "N1",
                    "name": "Locality1",
                    "easting": 12345,
                    "northing": 34567,
                    "admin_area_id": 9,
                    "district_id": 10,
                    "obj": locality,
                },
            ]
        ).set_index("gazetteer_id")

        # Test
        load_existing_localities(existing_localities)

        # Assert
        updated_locality = Locality.objects.all()[0]

        self.assertEqual(len(Locality.objects.all()), 1)
        self.assertEqual(updated_locality.gazetteer_id, "N1")
        self.assertEqual(updated_locality.name, "Locality1")
        self.assertEqual(updated_locality.easting, 12345)
        self.assertEqual(updated_locality.northing, 34567)
        self.assertEqual(updated_locality.admin_area_id, 9)
        # self.assertEqual(updated_locality.district_id, 10)
