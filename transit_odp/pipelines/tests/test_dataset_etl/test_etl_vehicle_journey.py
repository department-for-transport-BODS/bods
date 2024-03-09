from dateutil import tz
import pandas as pd
import pytest

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.transmodel.models import VehicleJourney

from waffle.testutils import override_flag

TZ = tz.gettz("Europe/London")


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractStandardServiceVehicleJourney(ExtractBaseTestCase):
    test_file = "data/test_vehicle_journeys/test_standard_service.xml"

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "departure_time": "08:14:00",
                    "journey_pattern_ref": "PB0000582:186-jp_1",
                    "line_ref": "WRAY:PB0000582:186:WF1",
                    "journey_code": "3681",
                    "vehicle_journey_code": "3681",
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
                    "departure_day_shift": False,
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "departure_time": "16:40:00",
                    "journey_pattern_ref": "PB0000582:186-jp_2",
                    "line_ref": "WRAY:PB0000582:186:WF1",
                    "journey_code": "3682",
                    "vehicle_journey_code": "3682",
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
                    "departure_day_shift": False,
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
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

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
                    "departure_day_shift": False,
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
                    "departure_day_shift": False,
                },
            ]
        ).set_index("file_id")
        vehicle_journey_expected[
            ["route_hash", "service_pattern_id"]
        ] = transformed.vehicle_journeys[["route_hash", "service_pattern_id"]].copy()
        self.assertTrue(
            check_frame_equal(transformed.vehicle_journeys, vehicle_journey_expected)
        )

        self.assertCountEqual(
            list(transformed.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    def test_load(self):
        extracted = self.trans_xchange_extractor.extract()
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
    test_file = "data/test_vehicle_journeys/test_flexible_service.xml"

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        flexible_vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "UZ000CALC:53M",
                    "departure_time": None,
                    "journey_pattern_ref": "UZ000CALC:53M-jp_1",
                    "line_ref": "CALC:UZ000CALC:53M:53M",
                    "journey_code": None,
                    "vehicle_journey_code": "vj_1",
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
                    "departure_day_shift": False,
                }
            ]
        ).set_index("file_id")
        vehicle_journey_expected = pd.DataFrame()

        self.assertTrue(
            check_frame_equal(extracted.vehicle_journeys, vehicle_journey_expected)
        )
        self.assertTrue(
            check_frame_equal(
                extracted.flexible_vehicle_journeys, flexible_vehicle_journey_expected
            )
        )

        self.assertCountEqual(
            list(extracted.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    @pytest.mark.skip
    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

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
                    "departure_day_shift": False,
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
        self.assertNotIn("service_pattern_id", transformed.vehicle_journeys.columns)
        self.assertNotIn("route_hash", transformed.vehicle_journeys.columns)

    @pytest.mark.skip
    def test_load(self):
        extracted = self.trans_xchange_extractor.extract()
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
    test_file = "data/test_vehicle_journeys/test_flexible_and_standard_service.xml"

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "UZ000WBCT:B1081",
                    "departure_time": "15:10:00",
                    "journey_pattern_ref": "UZ000WBCT:B1081-jp_3",
                    "line_ref": "ARBB:UZ000WBCT:B1081:123",
                    "journey_code": "1094",
                    "vehicle_journey_code": "vj_3",
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
                    "departure_day_shift": False,
                },
            ]
        ).set_index("file_id")

        flexible_vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PB0002032:467",
                    "departure_time": None,
                    "journey_pattern_ref": "PB0002032:467-jp_1",
                    "line_ref": "ARBB:PB0002032:467:53M",
                    "journey_code": None,
                    "vehicle_journey_code": "vj_1",
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
                    "departure_day_shift": False,
                },
                {
                    "file_id": file_id,
                    "service_code": "UZ000WOCT:216",
                    "departure_time": None,
                    "journey_pattern_ref": "UZ000WOCT:216-jp_2",
                    "line_ref": "ARBB:UZ000WOCT:216:53M",
                    "journey_code": None,
                    "vehicle_journey_code": "vj_2",
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
                    "departure_day_shift": False,
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(extracted.vehicle_journeys, vehicle_journey_expected)
        )
        self.assertTrue(
            check_frame_equal(
                extracted.flexible_vehicle_journeys, flexible_vehicle_journey_expected
            )
        )

        self.assertCountEqual(
            list(extracted.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    @pytest.mark.skip
    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

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
                    "departure_day_shift": False,
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
                    "departure_day_shift": False,
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
                    "departure_day_shift": False,
                },
            ]
        ).set_index("file_id")

        vehicle_journey_expected[
            ["route_hash", "service_pattern_id"]
        ] = transformed.vehicle_journeys[["route_hash", "service_pattern_id"]].copy()
        self.assertTrue(
            check_frame_equal(transformed.vehicle_journeys, vehicle_journey_expected)
        )

        self.assertCountEqual(
            list(transformed.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    def test_load(self):
        extracted = self.trans_xchange_extractor.extract()
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


@override_flag("is_timetable_visualiser_active", active=True)
class ETLVehicleJourneysWithDepartureDayShift(ExtractBaseTestCase):
    test_file = (
        "data/test_vehicle_journeys/test_vehicle_journeys_with_departure_day_shift.xml"
    )

    def test_extract(self):
        # setup
        file_id = self.trans_xchange_extractor.file_id

        # test
        extracted = self.trans_xchange_extractor.extract()

        vehicle_journey_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "departure_time": "08:14:00",
                    "journey_pattern_ref": "PB0000582:186-jp_1",
                    "line_ref": "WRAY:PB0000582:186:WF1",
                    "journey_code": "3681",
                    "vehicle_journey_code": "3681",
                    "departure_day_shift": True,
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "departure_time": "16:40:00",
                    "journey_pattern_ref": "PB0000582:186-jp_2",
                    "line_ref": "WRAY:PB0000582:186:WF1",
                    "journey_code": "3682",
                    "vehicle_journey_code": "3682",
                    "departure_day_shift": True,
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
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
        file_id = self.trans_xchange_extractor.file_id
        extracted = self.trans_xchange_extractor.extract()

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
                    "departure_day_shift": True,
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
                    "departure_day_shift": True,
                },
            ]
        ).set_index("file_id")

        vehicle_journey_expected[
            ["route_hash", "service_pattern_id"]
        ] = transformed.vehicle_journeys[["route_hash", "service_pattern_id"]].copy()

        self.assertTrue(
            check_frame_equal(transformed.vehicle_journeys, vehicle_journey_expected)
        )

        self.assertCountEqual(
            list(transformed.vehicle_journeys.columns),
            list(vehicle_journey_expected.columns),
        )

    def test_load(self):
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        # test
        self.feed_parser.load(transformed)

        vehicle_journeys = VehicleJourney.objects.all()

        self.assertEqual(2, vehicle_journeys.count())
        for journey in vehicle_journeys:
            self.assertEqual(journey.line_ref, "WRAY:PB0000582:186:WF1")
            self.assertIn(journey.journey_code, ["3681", "3682"])
