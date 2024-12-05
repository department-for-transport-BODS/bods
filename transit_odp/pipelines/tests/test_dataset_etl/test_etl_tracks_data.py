from dateutil import tz
import pandas as pd
import pytest

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.transmodel.models import (
    VehicleJourney,
    ServicePattern,
    ServicePatternStop,
)

from waffle.testutils import override_flag

TZ = tz.gettz("Europe/London")

@override_flag("is_timetable_visualiser_active", active=True)
@override_flag("extract_tracks_data", active=True)
class ExtractTracksData(ExtractBaseTestCase):
    test_file = "data/test_tracks/long_lat_tracks.xml"

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        tracks_data = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "departure_time": pd.to_timedelta("08:14:00"),
                    "journey_pattern_ref": "PB0000582:186-jp_1",
                    "line_ref": "WRAY:PB0000582:186:WF1",
                    "journey_code": "3681",
                    "vehicle_journey_code": "3681",
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
                    "wait_time": pd.NaT,
                    "departure_day_shift": False,
                    "block_number": None,
                    "vj_departure_time": pd.to_timedelta("08:14:00"),
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "departure_time": pd.to_timedelta("16:40:00"),
                    "journey_pattern_ref": "PB0000582:186-jp_2",
                    "line_ref": "WRAY:PB0000582:186:WF1",
                    "journey_code": "3682",
                    "vehicle_journey_code": "3682",
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
                    "wait_time": pd.NaT,
                    "departure_day_shift": False,
                    "block_number": None,
                    "vj_departure_time": pd.to_timedelta("16:40:00"),
                },
            ]
        ).set_index("file_id")
        print(extracted.journey_pattern_tracks)
        self.assertTrue(
            check_frame_equal(extracted.journey_pattern_tracks, tracks_data)
        )

        self.assertCountEqual(
            list(extracted.journey_pattern_tracks.columns),
            list(tracks_data.columns),
        )

    # def test_transform(self):
    #     # setup
    #     extracted = self.trans_xchange_extractor.extract()
    #     file_id = self.trans_xchange_extractor.file_id

    #     # test
    #     transformed = self.feed_parser.transform(extracted)

    #     vehicle_journey_expected = pd.DataFrame(
    #         [
    #             {
    #                 "file_id": file_id,
    #                 "departure_time": pd.to_timedelta("08:14:00"),
    #                 "journey_pattern_ref": "PB0000582:186-jp_1",
    #                 "line_ref": "WRAY:PB0000582:186:WF1",
    #                 "journey_code": "3681",
    #                 "vehicle_journey_code": "3681",
    #                 "service_code": "PB0000582:186",
    #                 "direction": "outbound",
    #                 "departure_day_shift": False,
    #                 "block_number": None,
    #                 "vj_departure_time": pd.to_timedelta("08:14:00"),
    #             },
    #             {
    #                 "file_id": file_id,
    #                 "departure_time": pd.to_timedelta("16:40:00"),
    #                 "journey_pattern_ref": "PB0000582:186-jp_2",
    #                 "line_ref": "WRAY:PB0000582:186:WF1",
    #                 "journey_code": "3682",
    #                 "vehicle_journey_code": "3682",
    #                 "service_code": "PB0000582:186",
    #                 "direction": "inbound",
    #                 "departure_day_shift": False,
    #                 "block_number": None,
    #                 "vj_departure_time": pd.to_timedelta("16:40:00"),
    #             },
    #         ]
    #     ).set_index("file_id")
    #     vehicle_journey_expected[
    #         ["route_hash", "service_pattern_id"]
    #     ] = transformed.vehicle_journeys[["route_hash", "service_pattern_id"]].copy()
    #     self.assertTrue(
    #         check_frame_equal(transformed.vehicle_journeys, vehicle_journey_expected)
    #     )

    #     self.assertCountEqual(
    #         list(transformed.vehicle_journeys.columns),
    #         list(vehicle_journey_expected.columns),
    #     )

    # def test_load(self):
    #     extracted = self.trans_xchange_extractor.extract()
    #     transformed = self.feed_parser.transform(extracted)

    #     # test
    #     self.feed_parser.load(transformed)

    #     vehicle_journeys = VehicleJourney.objects.all()

    #     self.assertEqual(2, vehicle_journeys.count())
    #     for journey in vehicle_journeys:
    #         self.assertEqual(journey.line_ref, "WRAY:PB0000582:186:WF1")
    #         self.assertIn(journey.journey_code, ["3681", "3682"])

