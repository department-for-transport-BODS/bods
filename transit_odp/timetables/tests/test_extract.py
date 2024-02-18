from dateutil import tz
import pandas as pd
import json

from transit_odp.timetables.tests.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.transmodel.models import ServicedOrganisations
from waffle.testutils import override_flag

TZ = tz.gettz("Europe/London")


@override_flag("is_timetable_visualiser_active", active=True)
class ETLTransXChangeExtractor(ExtractBaseTestCase):
    test_file = (
        "data/test_flexible_and_standard_service.xml"
    )

    def test_flexible_journey_pattern(self):
        # setup
        file_id = hash(self.file_obj.file)

        # test
        extracted = self.trans_xchange_extractor.extract()
        expected_flexible_journey_patterns = pd.DataFrame([
            {
                "journey_pattern_id": "jp_1",
                "service_code": "PB0002032:467",
                "file_id": file_id,
            },
            {
                "journey_pattern_id": "jp_2",
                "service_code": "UZ000WOCT:216",
                "file_id": file_id,
            }
        ]).set_index(["file_id","journey_pattern_id"])
        self.assertTrue(
            check_frame_equal(extracted.flexible_journey_patterns, expected_flexible_journey_patterns)
        )

    def test_create_flexible_timing_link(self):
        
        # setup
        flexible_journey_patterns = pd.DataFrame([{
            "file_id": "-4887190564465416312",
            "journey_pattern_id": "jp_1",
            "atco_code": "02903501",
            "bus_stop_type": "fixed_flexible", 
            "service_code": "PB0002032:467"
        },
        {
            "file_id": "-4887190564465416312",
            "journey_pattern_id": "jp_1",
            "atco_code": "02901353",
            "bus_stop_type": "flexible", 
            "service_code": "PB0002032:467"
        },
        {
            "file_id": "-4887190564465416312",
            "journey_pattern_id": "jp_2",
            "atco_code": "02901278",
            "bus_stop_type": "flexible", 
            "service_code": "UZ000WOCT:216"
        }])

        flexible_jp_to_jps = pd.DataFrame([{
            "file_id": "-4887190564465416312",
            "journey_pattern_id": "jp_1",
            "order": 0,
            "jp_section_ref": "-3768090454861795532"
        },
        {
            "file_id": "-4887190564465416312",
            "journey_pattern_id": "jp_2",
            "order": 1,
            "jp_section_ref": "-3859800699360366617"
        }])

        expected_flexible_timing_link = pd.DataFrame([{
            "order": 0,
            "from_stop_ref": "02903501",
            "to_stop_ref": "02901353",
        }])

        # test
        flexible_timing_links = self.trans_xchange_extractor.create_flexible_timing_link(flexible_journey_patterns, flexible_jp_to_jps)
        flexible_timing_links = flexible_timing_links.reset_index().reset_index()[["order", "from_stop_ref", "to_stop_ref"]]
        self.assertTrue(check_frame_equal(flexible_timing_links, expected_flexible_timing_link))


    def test_extract_flexible_journey_patterns(self):
        # setup
        file_id = hash(self.file_obj.file)
        expected_flexible_jp = pd.DataFrame([{
            "file_id": file_id,
            "journey_pattern_id": "jp_1",
            "atco_code": "02903501",
            "bus_stop_type": "fixed_flexible",
            "service_code": "PB0002032:467"
        },
        {
            "file_id": file_id,
            "journey_pattern_id": "jp_1",
            "atco_code": "02901353",
            "bus_stop_type": "flexible",
            "service_code": "PB0002032:467"
        },
        {
            "file_id": file_id,
            "journey_pattern_id": "jp_2",
            "atco_code": "02901278",
            "bus_stop_type": "flexible",
            "service_code": "UZ000WOCT:216"
        }]).set_index(["file_id", "journey_pattern_id"])

        # test
        extracted_flexible_journey_patterns = self.trans_xchange_extractor.extract_flexible_journey_patterns()
        self.assertTrue(check_frame_equal(extracted_flexible_journey_patterns, expected_flexible_jp))


    def test_create_flexible_jps(self):
        # setup
        flexible_journey_pattern = pd.DataFrame([{
            "file_id": "5303113700073932075",
            "journey_pattern_id": "jp_1",
            "atco_code": "02903501",
            "bus_stop_type": "fixed_flexible",
            "service_code": "PB0002032:467"
        },
        {
             "file_id": "5303113700073932075",
            "journey_pattern_id": "jp_1",
            "atco_code": "02901353",
            "bus_stop_type": "flexible",
            "service_code": "PB0002032:467"
        },
        {
             "file_id": "5303113700073932075",
            "journey_pattern_id": "jp_2",
            "atco_code": "02901278",
            "bus_stop_type": "flexible",
            "service_code": "UZ000WOCT:216"
        }])

        expected_flexible_jp_sections = pd.DataFrame([{
            "file_id": "5303113700073932075",
            "jp_section_id": "-8736408785585707534"
        },
        {
             "file_id": "5303113700073932075",
            "jp_section_id": "-8278724903796558663"
        }])

        expected_flexible_jp_to_jps = pd.DataFrame([{
             "file_id": "5303113700073932075",
             "journey_pattern_id": "jp_1",
             "order": 0,
        },
        {
             "file_id": "5303113700073932075",
             "journey_pattern_id": "jp_2",
             "order": 1,
        }])
        
        # test
        flexible_jp_sections, flexible_jp_to_jps = self.trans_xchange_extractor.create_flexible_jps(flexible_journey_pattern)
        flexible_jp_sections = flexible_jp_sections.reset_index().reset_index()[["file_id"]]
        flexible_jp_to_jps = flexible_jp_to_jps.reset_index().reset_index().reset_index()[["file_id", "journey_pattern_id", "order"]]
        self.assertTrue(check_frame_equal(flexible_jp_to_jps, expected_flexible_jp_to_jps))
        self.assertTrue(check_frame_equal(flexible_jp_sections, expected_flexible_jp_sections[["file_id"]]))