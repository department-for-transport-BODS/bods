import pandas as pd
import pandas.testing as pdt

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.transmodel.models import (
    Tracks,
    TracksVehicleJourney,
)

from waffle.testutils import override_flag


@override_flag("is_timetable_visualiser_active", active=True)
@override_flag("extract_tracks_data", active=True)
class ExtractTracksData(ExtractBaseTestCase):
    test_file = "data/test_tracks/long_lat_tracks.xml"

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id
        tracks_data = {
            "rl_ref": ["RL1", "RL2"],
            "rs_ref": ["RS1", "RS1"],
            "from_atco_code": ["0100BRP90310", "3290YYA00384"],
            "to_atco_code": ["3290YYA00384", "3290YYA00895"],
            "distance": ["1340", "1306"],
            "geometry": [
                [("-1.122750", "53.984560"), ("-1.122540", "53.984470")],
                [("-1.108960", "53.977150"), ("-1.108920", "53.977120")],
            ],
        }  # Create the DataFrame df = pd.DataFrame(data)
        route_map_data = {
            "route_ref": ["RT42", "RT43", "RT44"],
            "rs_ref": [["RS1"], ["RS1"], ["RS1"]],
            "jp_ref": [
                ["JP1", "JP2", "JP3", "JP4", "JP5", "JP6", "JP7"],
                ["JP8", "JP9", "JP10", "JP11", "JP12"],
                ["JP13"],
            ],
        }

        # Create the DataFrame
        route_map = pd.DataFrame(route_map_data)
        route_map["file_id"] = file_id
        tracks_df = pd.DataFrame(tracks_data)
        tracks_df["file_id"] = file_id
        tracks_df["rl_order"] = [1, 2]
        self.assertTrue(check_frame_equal(extracted.journey_pattern_tracks, tracks_df))
        self.assertTrue(check_frame_equal(extracted.route_map, route_map))

        self.assertCountEqual(
            list(extracted.journey_pattern_tracks.columns),
            list(tracks_df.columns),
        )
        self.assertAlmostEqual(
            list(extracted.route_map.columns), list(route_map.columns)
        )

    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        # test
        transformed = self.feed_parser.transform(extracted)
        jp_tracks = pd.DataFrame({"rl_order": [1, 2]})
        jp_tracks["file_id"] = file_id
        expected_jp_tracks = transformed.journey_pattern_tracks[["rl_order", "file_id"]]
        self.assertTrue(check_frame_equal(expected_jp_tracks, jp_tracks))
        self.assertTrue(check_frame_equal(expected_jp_tracks, jp_tracks))
        self.assertCountEqual(
            list(expected_jp_tracks.columns),
            list(jp_tracks.columns),
        )

    def test_load(self):
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)
        expected_tracks = {"track_id": [1, 2]}
        # test
        self.feed_parser.load(transformed)

        tracks = Tracks.objects.all()
        Tracks.objects
        for track in tracks:
            self.assertIn(track.from_atco_code, ["0100BRP90310", "3290YYA00384"])
        self.assertEqual(2, tracks.count())

        tracks_vj = TracksVehicleJourney.objects.all()
        data = list(tracks_vj.values())
        df = pd.DataFrame(data)
        # Group by tracks_id
        grouped = df.groupby("tracks_id")
        # Number of rows in each group
        actual_series = grouped.size()
        # Create the expected Series
        expected_series = pd.Series([310, 310], index=[1, 2])
        expected_series.index.names = ["tracks_id"]
        pdt.assert_series_equal(actual_series, expected_series)
