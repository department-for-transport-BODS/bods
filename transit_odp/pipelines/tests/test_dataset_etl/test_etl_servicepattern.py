import datetime
import os

import pandas as pd
from django.core.files import File
from django.test import TestCase
from waffle.testutils import override_flag

from transit_odp.naptan.factories import (
    AdminAreaFactory,
    DistrictFactory,
    LocalityFactory,
)
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.pipelines.pipelines.dataset_etl.feed_parser import FeedParser
from transit_odp.pipelines.tests.test_dataset_etl.helpers import (
    create_naptan_localities,
    create_naptan_stops,
)
from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.transmodel.models import ServicePattern


class ServicePatternTestCase(TestCase):
    def setUp(self):
        self.now = datetime.datetime.now()

        self.cur_dir = os.path.abspath(os.path.dirname(__file__))
        self.org = OrganisationFactory()
        self.admin_area = AdminAreaFactory()
        self.district = DistrictFactory()

        self.locality = LocalityFactory(
            district=self.district, admin_area=self.admin_area
        )

    def test_servicepattern(self):
        """
        Tests an xml file correctly generates a ServicePattern with the
        correct stop sequence.
        """

        # setup
        file = os.path.join(self.cur_dir, "data/test_servicepattern/test.xml")

        revision = DatasetRevisionFactory(
            dataset__organisation=self.org,
            is_published=False,
            status=FeedStatus.pending.value,
        )

        feed_progress = DatasetETLTaskResultFactory.create(revision=revision)

        self.feed_parser = FeedParser(revision, feed_progress)

        # We need naptan localities and stops
        localities = create_naptan_localities(
            self.feed_parser,
            File(file, name="test_file"),
            self.admin_area,
            self.district,
        )
        create_naptan_stops(
            self.feed_parser, File(file, name="test_file"), localities, self.admin_area
        )

        revision.associate_file(file)

        # test
        self.feed_parser.index_feed()

        # assert

        # Load the expected data
        df_expected = pd.read_csv(
            os.path.join(
                self.cur_dir, "data/test_servicepattern/expected_servicepattern.csv"
            )
        )
        df_stop_sequence = df_expected[["stop_atco"]]

        # We have only one service
        service = revision.services.all()[0]
        # Check that one of the service patterns matches our expected data
        found = False
        for service_pattern in service.service_patterns.all():
            found = True
            for index, stop in enumerate(service_pattern.service_pattern_stops.all()):
                expected_atco = df_stop_sequence.iat[index, 0]
                if stop.atco_code != expected_atco:
                    found = False
                    break
            if found:
                break

        self.assertTrue(found)


columns_lines = [
    "line_id",
    "line_name",
    "outbound_description",
    "inbound_description",
]

columns_service_patterns = [
    "service_code",
    "direction",
    "geometry",
    "localities",
    "admin_area_codes",
    "description",
    "line_name",
    "journey_code",
    "vehicle_journey_code",
]


@override_flag("is_timetable_visualiser_active", active=True)
class ETLServicePatterns(ExtractBaseTestCase):
    test_file = "data/test_servicepattern/test_etl_service_pattern.xml"

    def test_extract_lines(self):
        extracted = self.trans_xchange_extractor.extract()

        self.assertEqual(extracted.lines.shape[0], 2)

        self.assertCountEqual(
            list(extracted.lines.columns),
            columns_lines,
        )
        self.assertEqual(extracted.lines.index.names, ["file_id"])

    def test_tranform_service_patterns(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)

        self.assertEqual(transformed.service_patterns.shape[0], 7)

        self.assertCountEqual(
            list(transformed.service_patterns.columns),
            columns_service_patterns,
        )

    def test_load_service_patterns(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        service_patterns = ServicePattern.objects.all()
        service_service_patterns_through = ServicePattern.services.through.objects.all()
        # test

        self.assertEqual(7, service_patterns.count())
        self.assertEqual(7, service_service_patterns_through.count())

    def test_correct_description_based_on_direction_and_line(self):
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        service_patterns = transformed.service_patterns
        expected_desc_line_6 = "Harrogate - Pannal Ash Circular"
        expected_desc_line_x6 = "Harrogate - Beckwith Knowle Circular"

        filtered_rows_line_6 = service_patterns[
            (service_patterns["direction"] == "outbound")
            & (service_patterns["line_name"] == "6")
        ]
        filtered_rows_line_x6 = service_patterns[
            (service_patterns["direction"] == "outbound")
            & (service_patterns["line_name"] == "X6")
        ]

        # Check description for line 6
        for index, row in filtered_rows_line_6.iterrows():
            self.assertEqual(row["description"], expected_desc_line_6)

        # Check description for line X6
        for index, row in filtered_rows_line_x6.iterrows():
            self.assertEqual(row["description"], expected_desc_line_x6)
