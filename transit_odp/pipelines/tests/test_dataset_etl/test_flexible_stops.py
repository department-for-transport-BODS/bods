from dateutil import tz
import pandas as pd
import pytest

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal

from waffle.testutils import override_flag

from transit_odp.transmodel.models import ServicePattern, ServicePatternStop

TZ = tz.gettz("Europe/London")


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractFlexibleStops(ExtractBaseTestCase):
    test_file = "data/test_flexible_stops/test_flexible_stops.xml"

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        extracted_provisional_stops = extracted.provisional_stops

        # check the provisional stops column and geometry
        self.assertEqual(
            len(
                extracted_provisional_stops.loc[
                    extracted_provisional_stops.index == "270002700966", "geometry"
                ].iloc[0]
            ),
            4,
        )
        self.assertEqual(
            sorted(list(extracted_provisional_stops.columns)),
            sorted(["geometry", "locality", "common_name"]),
        )

        # check the extracted flexible stop points
        expected_flexible_stops = pd.DataFrame(
            [
                {
                    "atco_code": "270002700966",
                    "bus_stop_type": "fixed_flexible",
                },
                {
                    "atco_code": "030058880001",
                    "bus_stop_type": "flexible",
                },
                {
                    "atco_code": "030058870001",
                    "bus_stop_type": "fixed_flexible",
                },
                {
                    "atco_code": "030058860001",
                    "bus_stop_type": "flexible",
                },
            ]
        ).set_index("atco_code")
        extracted_flexible_stop_points = extracted.flexible_stop_points
        self.assertTrue(
            check_frame_equal(extracted_flexible_stop_points, expected_flexible_stops)
        )

        # check flexible journey patterns
        expected_flexible_journey_details = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "journey_pattern_id": "PB0002032:468-jp_1",
                    "atco_code": "270002700966",
                    "bus_stop_type": "fixed_flexible",
                    "service_code": "PB0002032:468",
                    "direction": "outbound",
                },
                {
                    "file_id": file_id,
                    "journey_pattern_id": "PB0002032:468-jp_1",
                    "atco_code": "030058880001",
                    "bus_stop_type": "flexible",
                    "service_code": "PB0002032:468",
                    "direction": "outbound",
                },
                {
                    "file_id": file_id,
                    "journey_pattern_id": "PB0002032:468-jp_1",
                    "atco_code": "030058870001",
                    "bus_stop_type": "fixed_flexible",
                    "service_code": "PB0002032:468",
                    "direction": "outbound",
                },
                {
                    "file_id": file_id,
                    "journey_pattern_id": "PB0002032:468-jp_1",
                    "atco_code": "030058860001",
                    "bus_stop_type": "flexible",
                    "service_code": "PB0002032:468",
                    "direction": "outbound",
                },
            ]
        ).set_index(["file_id", "journey_pattern_id"])
        extracted_flexible_journey_details = extracted.flexible_journey_details
        self.assertTrue(
            check_frame_equal(
                extracted_flexible_journey_details, expected_flexible_journey_details
            )
        )

    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)

        transformed_service_pattern_stops = transformed.service_pattern_stops
        self.assertEquals(
            sorted(list(transformed_service_pattern_stops.columns)),
            sorted(
                [
                    "service_pattern_id",
                    "order",
                    "stop_atco",
                    "departure_time",
                    "is_timing_status",
                    "journey_pattern_id",
                    "vehicle_journey_code",
                    "naptan_id",
                    "geometry",
                    "locality_id",
                    "admin_area_id",
                    "common_name",
                ]
            ),
        )
        transformed_service_patterns = transformed.service_patterns
        self.assertEquals(
            sorted(list(transformed_service_patterns.columns)),
            sorted(
                [
                    "service_code",
                    "from_stop_atco",
                    "to_stop_atco",
                    "geometry",
                    "localities",
                    "admin_area_codes",
                    "journey_pattern_id",
                    "vehicle_journey_code",
                ]
            ),
        )

        expected_service_links = pd.DataFrame(
            [
                {
                    "from_stop_atco": "270002700966",
                    "to_stop_atco": "030058880001",
                    "index": 0,
                },
                {
                    "from_stop_atco": "030058880001",
                    "to_stop_atco": "030058870001",
                    "index": 1,
                },
                {
                    "from_stop_atco": "030058870001",
                    "to_stop_atco": "030058860001",
                    "index": 2,
                },
            ]
        ).set_index(["from_stop_atco", "to_stop_atco"])

        self.assertTrue(
            check_frame_equal(transformed.service_links, expected_service_links)
        )


@override_flag("is_timetable_visualiser_active", active=False)
class ExtractFlexibleStopsWithVehicleJourneyWithoutFeature(ExtractBaseTestCase):
    test_file = "data/test_flexible_stops/test_flexible_stops_without_feature.xml"

    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        sp_stops = ServicePatternStop.objects.all()
        service_pattern = ServicePattern.objects.all()
        # test

        self.assertEqual(60, sp_stops.count())
        self.assertEqual(1, service_pattern.count())
