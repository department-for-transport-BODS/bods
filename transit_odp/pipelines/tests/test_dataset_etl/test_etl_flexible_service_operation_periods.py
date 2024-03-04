from dateutil import tz
import pandas as pd

import datetime

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from waffle.testutils import override_flag

from transit_odp.transmodel.models import FlexibleServiceOperationPeriod

TZ = tz.gettz("Europe/London")


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractFlexibleOperationPeriods(ExtractBaseTestCase):
    test_file = "data/test_vehicle_journeys/test_flexible_service.xml"

    def test_extract(self):
        # setup
        file_id = self.xml_file_parser.file_id

        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        expected_flexible_service_operation_period = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "vehicle_journey_code": "vj_1",
                    "start_time": "07:00:00",
                    "end_time": "12:00:00",
                },
                {
                    "file_id": file_id,
                    "vehicle_journey_code": "vj_1",
                    "start_time": "12:00:00",
                    "end_time": "19:00:00",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                extracted.flexible_operation_periods,
                expected_flexible_service_operation_period,
            )
        )

        self.assertCountEqual(
            list(extracted.flexible_operation_periods.columns),
            list(expected_flexible_service_operation_period.columns),
        )

    def test_transform(self):
        # setup
        file_id = self.xml_file_parser.file_id
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        expected_flexible_service_operation_period = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "vehicle_journey_code": "vj_1",
                    "start_time": "07:00:00",
                    "end_time": "12:00:00",
                },
                {
                    "file_id": file_id,
                    "vehicle_journey_code": "vj_1",
                    "start_time": "12:00:00",
                    "end_time": "19:00:00",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                transformed.flexible_operation_periods,
                expected_flexible_service_operation_period,
            )
        )

        self.assertCountEqual(
            list(transformed.flexible_operation_periods.columns),
            list(expected_flexible_service_operation_period.columns),
        )

    def test_load(self):
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        # test
        self.feed_parser.load(transformed)

        flexible_service_operation_periods = (
            FlexibleServiceOperationPeriod.objects.all()
        )

        self.assertEqual(2, flexible_service_operation_periods.count())
        for operation_period in flexible_service_operation_periods:
            self.assertIn(
                operation_period.start_time,
                [datetime.time(7, 0, 0), datetime.time(12, 0, 0)],
            )
            self.assertIn(
                operation_period.end_time,
                [datetime.time(12, 0, 0), datetime.time(19, 0, 0)],
            )
            self.assertIsNotNone(operation_period.vehicle_journey_id)


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractFlexibleOperationPeriodsForAllDayService(ExtractBaseTestCase):
    test_file = "data/test_vehicle_journeys/test_flexible_service_with_all_day.xml"

    def test_extract(self):
        # setup
        file_id = self.xml_file_parser.file_id
        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        expected_flexible_service_operation_period = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "vehicle_journey_code": "vj_1",
                    "start_time": None,
                    "end_time": None,
                }
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                extracted.flexible_operation_periods,
                expected_flexible_service_operation_period,
            )
        )

        self.assertCountEqual(
            list(extracted.flexible_operation_periods.columns),
            list(expected_flexible_service_operation_period.columns),
        )

    def test_transform(self):
        # setup
        file_id = self.xml_file_parser.file_id
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        expected_flexible_service_operation_period = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "vehicle_journey_code": "vj_1",
                    "start_time": None,
                    "end_time": None,
                }
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                transformed.flexible_operation_periods,
                expected_flexible_service_operation_period,
            )
        )

        self.assertCountEqual(
            list(transformed.flexible_operation_periods.columns),
            list(expected_flexible_service_operation_period.columns),
        )

    def test_load(self):
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        # test
        self.feed_parser.load(transformed)

        flexible_service_operation_periods = (
            FlexibleServiceOperationPeriod.objects.all()
        )

        self.assertEqual(1, flexible_service_operation_periods.count())
        for operation_period in flexible_service_operation_periods:
            self.assertIsNone(operation_period.start_time)
            self.assertIsNone(operation_period.end_time)
            self.assertIsNotNone(operation_period.vehicle_journey_id)


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractFlexibleOperationPeriodsWithStandardService(ExtractBaseTestCase):
    test_file = "data/test_vehicle_journeys/test_flexible_and_standard_service.xml"

    def test_extract(self):
        # setup
        file_id = self.xml_file_parser.file_id
        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        expected_flexible_service_operation_period = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "vehicle_journey_code": "vj_1",
                    "start_time": "07:00:00",
                    "end_time": "19:00:00",
                },
                {
                    "file_id": file_id,
                    "vehicle_journey_code": "vj_2",
                    "start_time": "07:00:00",
                    "end_time": "19:00:00",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                extracted.flexible_operation_periods,
                expected_flexible_service_operation_period,
            )
        )

        self.assertCountEqual(
            list(extracted.flexible_operation_periods.columns),
            list(expected_flexible_service_operation_period.columns),
        )

    def test_transform(self):
        # setup
        file_id = self.xml_file_parser.file_id
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        expected_flexible_service_operation_period = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "vehicle_journey_code": "vj_1",
                    "start_time": "07:00:00",
                    "end_time": "19:00:00",
                },
                {
                    "file_id": file_id,
                    "vehicle_journey_code": "vj_2",
                    "start_time": "07:00:00",
                    "end_time": "19:00:00",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                transformed.flexible_operation_periods,
                expected_flexible_service_operation_period,
            )
        )

        self.assertCountEqual(
            list(transformed.flexible_operation_periods.columns),
            list(expected_flexible_service_operation_period.columns),
        )

    def test_load(self):
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        # test
        self.feed_parser.load(transformed)

        flexible_service_operation_periods = (
            FlexibleServiceOperationPeriod.objects.all()
        )

        self.assertEqual(2, flexible_service_operation_periods.count())
        for operation_period in flexible_service_operation_periods:
            self.assertIn(
                operation_period.start_time,
                [datetime.time(7, 0, 0), datetime.time(19, 0, 0)],
            )
            self.assertIn(
                operation_period.end_time,
                [datetime.time(7, 0, 0), datetime.time(19, 0, 0)],
            )
            self.assertIsNotNone(operation_period.vehicle_journey_id)
