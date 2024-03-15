from waffle.testutils import override_flag

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
import pandas as pd

from transit_odp.transmodel.models import ServicePatternStop


@override_flag("is_timetable_visualiser_active", active=True)
class ETLSPSWithRunTimeInVehicleJourney(ExtractBaseTestCase):
    test_file = (
        "data/test_servicepatternstops/test_extract_sps_runtime_in_vj_timings.xml"
    )

    def test_extract(self):
        # setup
        file_id = self.trans_xchange_extractor.file_id
        # test
        extracted = self.trans_xchange_extractor.extract()
        extracted_timing_links = extracted.timing_links.reset_index()
        extracted_vehicle_journeys = extracted.vehicle_journeys.reset_index()

        condition_departure_time_1 = (
            (extracted_vehicle_journeys["journey_pattern_ref"] == "PF0007157:12-JP2")
            & (extracted_vehicle_journeys["file_id"] == file_id)
            & (extracted_vehicle_journeys["vehicle_journey_code"] == "VJ1")
        )
        condition_departure_time_2 = (
            (extracted_vehicle_journeys["journey_pattern_ref"] == "PF0007157:12-JP16")
            & (extracted_vehicle_journeys["file_id"] == file_id)
            & (extracted_vehicle_journeys["vehicle_journey_code"] == "VJ116")
        )
        departure_time_vj_1 = pd.unique(
            extracted_vehicle_journeys[condition_departure_time_1]["departure_time"]
        )
        departure_time_vj_2 = pd.unique(
            extracted_vehicle_journeys[condition_departure_time_2]["departure_time"]
        )

        self.assertIn("common_name", extracted.stop_points.columns)
        self.assertIn("is_timing_status", extracted.timing_links.columns)
        self.assertIn("run_time", extracted.timing_links.columns)
        self.assertIn("wait_time", extracted.timing_links.columns)
        self.assertIn("run_time", extracted.vehicle_journeys.columns)
        self.assertIn("departure_time", extracted.vehicle_journeys.columns)
        self.assertEqual(
            27,
            extracted_timing_links[
                extracted_timing_links["is_timing_status"] == True
            ].shape[0],
        )
        self.assertEqual(
            531,
            extracted_vehicle_journeys[
                extracted_vehicle_journeys["run_time"] == pd.to_timedelta("00:02:00")
            ].shape[0],
        )

        self.assertEqual(["07:05:00"], departure_time_vj_1)
        self.assertEqual(["20:00:00"], departure_time_vj_2)

    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)
        transformed_service_pattern_stops = (
            transformed.service_pattern_stops.reset_index()
        )
        condition_departure_time_1 = (
            transformed_service_pattern_stops["order"] == 33
        ) & (transformed_service_pattern_stops["stop_atco"] == "260007437")
        condition_departure_time_2 = (
            transformed_service_pattern_stops["order"] == 20
        ) & (transformed_service_pattern_stops["stop_atco"] == "260006542")
        departure_time_1 = transformed_service_pattern_stops[condition_departure_time_1]
        departure_time_2 = transformed_service_pattern_stops[condition_departure_time_2]

        self.assertNotIn("common_name", transformed.stop_points.columns)
        self.assertEqual(
            73,
            transformed_service_pattern_stops[
                transformed_service_pattern_stops["is_timing_status"] == True
            ].shape[0],
        )
        self.assertIn("18:15:00", departure_time_1["departure_time"].to_list())
        self.assertEqual(["07:15:00"], departure_time_2["departure_time"].to_list())

    def test_load(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        sp_stops = ServicePatternStop.objects.all()
        # test

        self.assertEqual(376, sp_stops.count())


@override_flag("is_timetable_visualiser_active", active=True)
class ETLSPSWithRunTimeInJourney(ExtractBaseTestCase):
    test_file = (
        "data/test_servicepatternstops/test_extract_sps_runtime_in_jp_timings.xml"
    )

    def test_extract(self):
        # setup
        file_id = self.trans_xchange_extractor.file_id
        # test
        extracted = self.trans_xchange_extractor.extract()
        extracted_timing_links = extracted.timing_links.reset_index()
        extracted_vehicle_journeys = extracted.vehicle_journeys.reset_index()

        condition_departure_time_1 = (
            (extracted_vehicle_journeys["journey_pattern_ref"] == "PK1109969:8-jp_1")
            & (extracted_vehicle_journeys["file_id"] == file_id)
            & (extracted_vehicle_journeys["vehicle_journey_code"] == "vj_1")
        )
        condition_departure_time_2 = (
            (extracted_vehicle_journeys["journey_pattern_ref"] == "PK1109969:8-jp_2")
            & (extracted_vehicle_journeys["file_id"] == file_id)
            & (extracted_vehicle_journeys["vehicle_journey_code"] == "vj_20")
        )
        departure_time_vj_1 = pd.unique(
            extracted_vehicle_journeys[condition_departure_time_1]["departure_time"]
        )
        departure_time_vj_2 = pd.unique(
            extracted_vehicle_journeys[condition_departure_time_2]["departure_time"]
        )

        self.assertIn("common_name", extracted.stop_points.columns)
        self.assertIn("is_timing_status", extracted.timing_links.columns)
        self.assertIn("run_time", extracted.timing_links.columns)
        self.assertIn("wait_time", extracted.timing_links.columns)
        self.assertIn("run_time", extracted.vehicle_journeys.columns)
        self.assertIn("departure_time", extracted.vehicle_journeys.columns)
        self.assertEqual(
            44,
            extracted_timing_links[
                extracted_timing_links["is_timing_status"] == True
            ].shape[0],
        )
        self.assertEqual(
            0,
            extracted_vehicle_journeys[
                extracted_vehicle_journeys["run_time"] == pd.to_timedelta("00:02:00")
            ].shape[0],
        )
        self.assertEqual(
            18,
            extracted_timing_links[
                extracted_timing_links["run_time"] == pd.to_timedelta("00:02:00")
            ].shape[0],
        )
        self.assertEqual(
            120,
            extracted_timing_links[
                extracted_timing_links["run_time"] == pd.to_timedelta("00:01:00")
            ].shape[0],
        )

        self.assertEqual(["07:40:00"], departure_time_vj_1)
        self.assertEqual(["16:13:00"], departure_time_vj_2)

    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)
        transformed_service_pattern_stops = (
            transformed.service_pattern_stops.reset_index()
        )
        condition_departure_time_1 = (
            transformed_service_pattern_stops["order"] == 55
        ) & (transformed_service_pattern_stops["stop_atco"] == "40004407400B")
        condition_departure_time_2 = (
            transformed_service_pattern_stops["order"] == 56
        ) & (transformed_service_pattern_stops["stop_atco"] == "40004404140C")
        departure_time_1 = transformed_service_pattern_stops[condition_departure_time_1]
        departure_time_2 = transformed_service_pattern_stops[condition_departure_time_2]

        self.assertNotIn("common_name", transformed.stop_points.columns)
        self.assertEqual(
            47,
            transformed_service_pattern_stops[
                transformed_service_pattern_stops["is_timing_status"] == True
            ].shape[0],
        )
        self.assertIn("19:12:00", departure_time_1["departure_time"].to_list())
        self.assertEqual(["08:40:00"], departure_time_2["departure_time"].to_list())

    def test_load(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        sp_stops = ServicePatternStop.objects.all()
        # test

        self.assertEqual(169, sp_stops.count())


@override_flag("is_timetable_visualiser_active", active=True)
class ETLSPSWithSyntheticStop(ExtractBaseTestCase):
    test_file = "data/test_servicepatternstops/test_extract_sps_synthetic_stop.xml"
    ignore_stops = ["340001671OPP"]

    def test_load(self):
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)
        self.feed_parser.load(transformed)
        sps_common_name = ServicePatternStop.objects.values_list(
            "txc_common_name", flat=True
        )

        self.assertIn("Harpsden Turn", sps_common_name)
        self.assertNotIn("Bell Street", sps_common_name)


@override_flag("is_timetable_visualiser_active", active=True)
class ETLSPSWithProvisionalStop(ExtractBaseTestCase):
    test_file = "data/test_servicepatternstops/test_extract_sps_provisional_stop.xml"
    ignore_stops = ["111", "222"]

    def test_load(self):
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        atco_codes = ["111", "222"]
        common_names = ["FirstCommonName", "SecondCommonName"]
        extracted_stops = extracted.provisional_stops.reset_index()
        transformed_stop_points = transformed.stop_points.reset_index()
        provisional_stops = transformed_stop_points[
            transformed_stop_points["atco_code"].isin(atco_codes)
        ]

        self.assertEqual(atco_codes, extracted_stops["atco_code"].to_list())
        self.assertEqual(common_names, extracted_stops["common_name"].to_list())
        self.assertEqual(atco_codes, provisional_stops["atco_code"].to_list())
