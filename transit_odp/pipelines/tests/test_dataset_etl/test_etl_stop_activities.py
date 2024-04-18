from dateutil import tz
import pytest
from waffle.testutils import override_flag
from django.test import TransactionTestCase

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.transmodel.factories import StopActivityFactory
from transit_odp.transmodel.models import StopActivity

import pandas as pd

pytestmark = pytest.mark.django_db

TZ = tz.gettz("Europe/London")


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractStandardStopActivities(ExtractBaseTestCase):
    test_file = "data/test_stop_activity/test_standard_service.xml"


    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()

        from_activities = extracted.timing_links["from_activity_id"]
        to_activities = extracted.timing_links["to_activity_id"]

        self.assertFalse(from_activities.empty)
        self.assertFalse(to_activities.empty)

        self.assertFalse(from_activities.isna().any())
        self.assertFalse(to_activities.isna().any())

        self.assertEqual(from_activities.shape[0], 19)
        self.assertEqual(to_activities.shape[0], 19)

    def test_transform(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        activities = transformed.service_pattern_stops[["activity_id", "stop_atco"]]

        self.assertFalse(activities["activity_id"].empty)
        self.assertFalse(activities["activity_id"].isna().any())
        self.assertEqual(activities.shape[0], 21)
        self.assertEqual(
            activities[activities["stop_atco"] == "450029899"]["activity_id"].iloc[0], 8
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "450050590"]["activity_id"].iloc[0], 4
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "450014638"]["activity_id"].iloc[0], 3
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "450018433"]["activity_id"].iloc[0], 1
        )


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractFlexibleStopActivities(ExtractBaseTestCase):
    test_file = "data/test_stop_activity/test_flexible_stop_activity.xml"

    @pytest.fixture(autouse=True)
    def setup(self, setup_stop_activities):
        pass

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()

        activities = extracted.flexible_journey_details["activity_id"]
        self.assertFalse(activities.empty)

        self.assertFalse(activities.isna().any())

        self.assertEqual(activities.shape[0], 9)

    def test_transform(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        activities = transformed.service_pattern_stops[["activity_id", "stop_atco"]]

        self.assertFalse(activities["activity_id"].empty)
        self.assertFalse(activities["activity_id"].isna().any())
        self.assertEqual(activities.shape[0], 9)
        self.assertEqual(
            activities[activities["stop_atco"] == "270002700966"]["activity_id"].iloc[
                0
            ],
            2,
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "030058880001"]["activity_id"].iloc[
                0
            ],
            4,
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "030058870001"]["activity_id"].iloc[
                0
            ],
            1,
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "030058860001"]["activity_id"].iloc[
                0
            ],
            3,
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "02901278"]["activity_id"].iloc[0],
            2,
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "02901279"]["activity_id"].iloc[0],
            1,
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "030058880001"]["activity_id"].iloc[
                0
            ],
            4,
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "030058870001"]["activity_id"].iloc[
                0
            ],
            1,
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "030058860001"]["activity_id"].iloc[
                0
            ],
            3,
        )


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractFlexibleAndStandardStopActivities(ExtractBaseTestCase):
    test_file = "data/test_stop_activity/test_flexible_and_standard_service.xml"

    @pytest.fixture(autouse=True)
    def setup(self, setup_stop_activities):
        pass

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()

        from_activities = extracted.timing_links["from_activity_id"]
        to_activities = extracted.timing_links["to_activity_id"]
        flex_activities = extracted.flexible_journey_details["activity_id"]

        self.assertFalse(from_activities.empty)
        self.assertFalse(to_activities.empty)
        self.assertFalse(from_activities.isna().any())
        self.assertFalse(to_activities.isna().any())
        self.assertEqual(from_activities.shape[0], 9)
        self.assertEqual(to_activities.shape[0], 9)

        self.assertFalse(flex_activities.empty)
        self.assertEqual(flex_activities.shape[0], 3)

    def test_transform(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        activities = transformed.service_pattern_stops[["activity_id", "stop_atco"]]

        self.assertFalse(activities["activity_id"].empty)
        self.assertFalse(activities["activity_id"].isna().any())
        self.assertEqual(activities.shape[0], 11)
        self.assertEqual(
            activities[activities["stop_atco"] == "02903617"]["activity_id"].iloc[0], 3
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "02903501"]["activity_id"].iloc[0], 2
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "02901353"]["activity_id"].iloc[0], 3
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "02900018"]["activity_id"].iloc[0], 2
        )
        self.assertEqual(
            activities[activities["stop_atco"] == "02901049"]["activity_id"].iloc[0], 1
        )
