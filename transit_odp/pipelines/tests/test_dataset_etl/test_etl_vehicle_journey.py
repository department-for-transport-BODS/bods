from dateutil import tz
import pandas as pd
from transit_odp.pipelines.pipelines.dataset_etl.utils.extract_meta_result import (
    ETLReport,
)

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.transmodel.models import VehicleJourney

from waffle.testutils import override_flag
from django.test import override_settings

TZ = tz.gettz("Europe/London")


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractStandardServiceVehicleJourney(ExtractBaseTestCase):
    test_file = "data/vehicle_journeys/test_standard_service.xml"

    def test_extract(self):
        # setup
        file_id = hash(self.file_obj.file)

        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "departure_time": "08:14:00",
                    "journey_pattern_ref": "PB0000582:186-jp_1",
                    "line_ref": "WRAY:PB0000582:186:WF1",
                    "journey_code": "3681",
                    "vehicle_journey_code": "3681",
                },
                {
                    "file_id": file_id,
                    "departure_time": "16:40:00",
                    "journey_pattern_ref": "PB0000582:186-jp_2",
                    "line_ref": "WRAY:PB0000582:186:WF1",
                    "journey_code": "3682",
                    "vehicle_journey_code": "3682",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(extracted.vehicle_journeys, vehicle_journey_expected)
        )

        self.assertCountEqual(
            list(extracted.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    def test_transform(self):
        # setup
        file_id = hash(self.file_obj.file)
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "departure_time": "08:14:00",
                    "journey_pattern_ref": "PB0000582:186-jp_1",
                    "line_ref": "WRAY:PB0000582:186:WF1",
                    "journey_code": "3681",
                    "vehicle_journey_code": "3681",
                    "service_code": "PB0000582:186",
                    "direction": "outbound",
                },
                {
                    "file_id": file_id,
                    "departure_time": "16:40:00",
                    "journey_pattern_ref": "PB0000582:186-jp_2",
                    "line_ref": "WRAY:PB0000582:186:WF1",
                    "journey_code": "3682",
                    "vehicle_journey_code": "3682",
                    "service_code": "PB0000582:186",
                    "direction": "inbound",
                },
            ]
        ).set_index("file_id")
        self.assertTrue(
            check_frame_equal(transformed.vehicle_journeys, vehicle_journey_expected)
        )

        self.assertCountEqual(
            list(transformed.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    def test_load(self):
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        # test
        self.feed_parser.load(transformed)

        vehicle_journeys = VehicleJourney.objects.all()

        self.assertEqual(2, vehicle_journeys.count())
        for journey in vehicle_journeys:
            self.assertEqual(journey.line_ref, "WRAY:PB0000582:186:WF1")
            self.assertIn(journey.journey_code, ["3681", "3682"])


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractFlexibleServiceVehicleJourney(ExtractBaseTestCase):
    test_file = "data/vehicle_journeys/test_flexible_service.xml"

    def test_extract(self):
        # setup
        file_id = hash(self.file_obj.file)

        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "departure_time": None,
                    "journey_pattern_ref": "UZ000CALC:53M-jp_1",
                    "line_ref": "CALC:UZ000CALC:53M:53M",
                    "journey_code": None,
                    "vehicle_journey_code": "vj_1",
                }
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(extracted.vehicle_journeys, vehicle_journey_expected)
        )

        self.assertCountEqual(
            list(extracted.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    def test_transform(self):
        # setup
        file_id = hash(self.file_obj.file)
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "departure_time": None,
                    "journey_pattern_ref": "UZ000CALC:53M-jp_1",
                    "line_ref": "CALC:UZ000CALC:53M:53M",
                    "journey_code": None,
                    "vehicle_journey_code": "vj_1",
                    "service_code": "UZ000CALC:53M",
                    "direction": "inbound",
                },
            ]
        ).set_index("file_id")
        self.assertTrue(
            check_frame_equal(transformed.vehicle_journeys, vehicle_journey_expected)
        )

        self.assertCountEqual(
            list(transformed.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    def test_load(self):
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        # test
        self.feed_parser.load(transformed)

        vehicle_journeys = VehicleJourney.objects.all()

        self.assertEqual(1, vehicle_journeys.count())
        for journey in vehicle_journeys:
            self.assertEqual(journey.line_ref, "CALC:UZ000CALC:53M:53M")
            self.assertEqual(journey.journey_code, None)


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractFlexibleAndStandardServiceVehicleJourney(ExtractBaseTestCase):
    test_file = "data/vehicle_journeys/test_flexible_and_standard_service.xml"

    def test_extract(self):
        # setup
        file_id = hash(self.file_obj.file)

        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "departure_time": "15:10:00",
                    "journey_pattern_ref": "UZ000WBCT:B1081-jp_3",
                    "line_ref": "ARBB:UZ000WBCT:B1081:123",
                    "journey_code": "1094",
                    "vehicle_journey_code": "vj_3",
                },
                {
                    "file_id": file_id,
                    "departure_time": None,
                    "journey_pattern_ref": "PB0002032:467-jp_1",
                    "line_ref": "ARBB:PB0002032:467:53M",
                    "journey_code": None,
                    "vehicle_journey_code": "vj_1",
                },
                {
                    "file_id": file_id,
                    "departure_time": None,
                    "journey_pattern_ref": "UZ000WOCT:216-jp_2",
                    "line_ref": "ARBB:UZ000WOCT:216:53M",
                    "journey_code": None,
                    "vehicle_journey_code": "vj_2",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(extracted.vehicle_journeys, vehicle_journey_expected)
        )

        self.assertCountEqual(
            list(extracted.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    def test_transform(self):
        # setup
        file_id = hash(self.file_obj.file)
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "departure_time": "15:10:00",
                    "journey_pattern_ref": "UZ000WBCT:B1081-jp_3",
                    "line_ref": "ARBB:UZ000WBCT:B1081:123",
                    "journey_code": "1094",
                    "vehicle_journey_code": "vj_3",
                    "service_code": "UZ000WBCT:B1081",
                    "direction": "inbound",
                },
                {
                    "file_id": file_id,
                    "departure_time": None,
                    "journey_pattern_ref": "PB0002032:467-jp_1",
                    "line_ref": "ARBB:PB0002032:467:53M",
                    "journey_code": None,
                    "vehicle_journey_code": "vj_1",
                    "service_code": "PB0002032:467",
                    "direction": "outbound",
                },
                {
                    "file_id": file_id,
                    "departure_time": None,
                    "journey_pattern_ref": "UZ000WOCT:216-jp_2",
                    "line_ref": "ARBB:UZ000WOCT:216:53M",
                    "journey_code": None,
                    "vehicle_journey_code": "vj_2",
                    "service_code": "UZ000WOCT:216",
                    "direction": "outbound",
                },
            ]
        ).set_index("file_id")
        self.assertTrue(
            check_frame_equal(transformed.vehicle_journeys, vehicle_journey_expected)
        )

        self.assertCountEqual(
            list(transformed.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    def test_load(self):
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        # test
        self.feed_parser.load(transformed)

        vehicle_journeys = VehicleJourney.objects.all()

        self.assertEqual(3, vehicle_journeys.count())
        for journey in vehicle_journeys:
            self.assertIn(
                journey.line_ref,
                [
                    "ARBB:UZ000WBCT:B1081:123",
                    "ARBB:PB0002032:467:53M",
                    "ARBB:UZ000WOCT:216:53M",
                ],
            )
            self.assertIn(journey.journey_code, ["1094", None])
