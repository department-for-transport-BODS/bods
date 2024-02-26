from dateutil import tz
import pandas as pd

from transit_odp.timetables.tests.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from waffle.testutils import override_flag

TZ = tz.gettz("Europe/London")


@override_flag("is_timetable_visualiser_active", active=True)
class ETLTransXChangeExtractor(ExtractBaseTestCase):
    test_file = "data/test_flexible_and_standard_service.xml"

    def test_fextract_flexible_journey_details(self):
        # setup
        file_id = self.trans_xchange_extractor.file_id

        # test
        extracted = self.trans_xchange_extractor.extract()
        expected_flexible_journey_patterns = pd.DataFrame(
            [
                {
                    "journey_pattern_id": "PB0002032:467-jp_1",
                    "service_code": "PB0002032:467",
                    "file_id": file_id,
                    "direction": "outbound",
                },
                {
                    "journey_pattern_id": "UZ000WOCT:216-jp_2",
                    "service_code": "UZ000WOCT:216",
                    "file_id": file_id,
                    "direction": "outbound",
                },
            ]
        ).set_index(["file_id", "journey_pattern_id"])
        self.assertTrue(
            check_frame_equal(
                extracted.flexible_journey_patterns, expected_flexible_journey_patterns
            )
        )

    def test_extract_flexible_journey_patterns(self):
        # setup
        file_id = self.trans_xchange_extractor.file_id
        expected_flexible_jp_details = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "journey_pattern_id": "PB0002032:467-jp_1",
                    "atco_code": "02903501",
                    "bus_stop_type": "fixed_flexible",
                    "service_code": "PB0002032:467",
                    "direction": "outbound",
                },
                {
                    "file_id": file_id,
                    "journey_pattern_id": "PB0002032:467-jp_1",
                    "atco_code": "02901353",
                    "bus_stop_type": "flexible",
                    "service_code": "PB0002032:467",
                    "direction": "outbound",
                },
                {
                    "file_id": file_id,
                    "journey_pattern_id": "UZ000WOCT:216-jp_2",
                    "atco_code": "02901278",
                    "bus_stop_type": "flexible",
                    "service_code": "UZ000WOCT:216",
                    "direction": "outbound",
                },
            ]
        ).set_index(["file_id", "journey_pattern_id"])

        # test
        extracted_flexible_journey_details = (
            self.trans_xchange_extractor.extract_flexible_journey_details()
        )
        self.assertTrue(
            check_frame_equal(
                extracted_flexible_journey_details, expected_flexible_jp_details
            )
        )
