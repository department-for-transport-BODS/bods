import os
from datetime import date, datetime
from unittest import skip

import pandas as pd
import pytest
from dateutil import tz
from dateutil.parser import parse
from ddt import data, ddt, unpack
from django.contrib.gis.geos import Point
from django.core.files import File
from django.test import TestCase
from unittest.mock import patch, MagicMock
from waffle.testutils import override_flag

from waffle.testutils import override_flag
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.naptan.models import AdminArea, District, Locality, StopPoint
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models.data import DatasetRevision
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.pipelines.pipelines.dataset_etl.feed_parser import FeedParser
from transit_odp.pipelines.pipelines.dataset_etl.utils.dataframes import (
    get_stop_activities,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.transform import (
    agg_service_pattern_sequences,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import TransformedData
from transit_odp.pipelines.pipelines.dataset_etl.utils.extract_meta_result import (
    ETLReport,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.timetables.extract import TransXChangeExtractor
from transit_odp.timetables.loaders import TransXChangeDataLoader
from transit_odp.transmodel.factories import ServiceFactory
from transit_odp.transmodel.models import (
    BookingArrangements,
    Service,
    ServiceLink,
    ServicePatternStop,
)
from transit_odp.xmltoolkit.xml_toolkit import XmlToolkit

TZ = tz.gettz("Europe/London")
EMPTY_TIMESTAMP = None


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractBaseTestCase(TestCase):
    """Loads required stop data onto naptan StopPoint table
    to ensure these stops are available when the table is
    queried while syncing stops with naptan stops
    """

    test_file: str
    ignore_stops = []
    ignore_provisional_stops = []
    allow_provisional_stops_in_naptan = False

    def setUp(self):
        self.cur_dir = os.path.abspath(os.path.dirname(__file__))

        # Create an organisation
        organisation = OrganisationFactory()

        # Create a feed
        self.revision = DatasetRevisionFactory(
            dataset__organisation=organisation,
            is_published=False,
            status=FeedStatus.pending.value,
        )

        # FeedParser performs the metadata extraction
        feed_progress = DatasetETLTaskResultFactory(revision=self.revision)
        self.feed_parser = FeedParser(self.revision, feed_progress)
        self.now = self.feed_parser.now

        xml_toolkit = XmlToolkit({"x": "http://www.transxchange.org.uk/"})
        self.xml_file_parser = self.feed_parser.extractor

        # Test file
        self.file_obj = File(os.path.join(self.cur_dir, self.test_file))
        self.doc, result = xml_toolkit.parse_xml_file(self.file_obj.file)

        self.trans_xchange_extractor = TransXChangeExtractor(
            self.file_obj, self.now, stop_activity_cache=get_stop_activities()
        )

        # Create bogus admin area
        self.admin = AdminAreaFactory(
            name="admin1",
            traveline_region_id="1",
            atco_code="1",
        )
        self.admin.save()

        # Create bogus district
        self.district = District(
            name="district1",
        )
        self.district.save()

        # Create the naptan StopPoints
        xml_stoppointrefs = xml_toolkit.get_elements(
            self.doc.getroot(), "/x:TransXChange/x:StopPoints/x:AnnotatedStopPointRef"
        )
        for xml_stoppointref in xml_stoppointrefs:
            locality_name = xml_toolkit.get_child_text(
                xml_stoppointref, "x:LocalityName"
            )
            stoppoint_naptan = xml_toolkit.get_child_text(
                xml_stoppointref, "x:StopPointRef"
            )

            if not self.ignore_stops or stoppoint_naptan not in self.ignore_stops:
                common_name = xml_toolkit.get_child_text(
                    xml_stoppointref, "x:CommonName"
                )
                if locality_name:
                    stoppoint = StopPoint(
                        naptan_code=stoppoint_naptan,
                        atco_code=stoppoint_naptan,
                        common_name=common_name,
                        location=Point(0, 0),
                        locality=self.get_locality(locality_name),
                        admin_area=self.admin,
                    )
                    stoppoint.save()

        xml_provisional_stoppointrefs = xml_toolkit.get_elements(
            self.doc.getroot(), "/x:TransXChange/x:StopPoints/x:StopPoint"
        )
        # insert locality for provisional stops
        for provisional_stop in xml_provisional_stoppointrefs:
            locality_ref = xml_toolkit.get_child_text(
                provisional_stop, "x:Place/x:NptgLocalityRef"
            )
            db_locality = self.get_locality(name=locality_ref)
            if self.allow_provisional_stops_in_naptan:
                stoppoint_naptan = xml_toolkit.get_child_text(
                    provisional_stop, "x:AtcoCode"
                )
                if (
                    not self.ignore_provisional_stops
                    or stoppoint_naptan not in self.ignore_provisional_stops
                ):
                    common_name = xml_toolkit.get_child_text(
                        provisional_stop, "x:Descriptor/x:CommonName"
                    )
                    stoppoint = StopPoint(
                        naptan_code=stoppoint_naptan,
                        atco_code=stoppoint_naptan,
                        common_name=common_name,
                        location=Point(0, 0),
                        locality=db_locality,
                        admin_area=self.admin,
                    )
                    stoppoint.save()

    # Get or create a locality by name
    def get_locality(self, name: str):
        try:
            locality = Locality.objects.get(name=name)
        except Locality.DoesNotExist:
            locality = Locality(
                gazetteer_id=name[:8],  # Just use the name as the gazetteer
                name=name,
                district=self.district,
                admin_area=self.admin,
                easting=1,
                northing=1,
                # last_change=self.now,
            )
            locality.save()
        return locality


@ddt
@override_flag("is_timetable_visualiser_active", active=True)
class ExtractMetadataTestCase(ExtractBaseTestCase):
    test_file = "data/test_extract_metadata.xml"

    @data(
        # A single feed that is not expiring
        ([EMPTY_TIMESTAMP], [None, None]),
        # A single feed with a declared expiry date
        (
            [datetime(2018, 11, 1, tzinfo=TZ)],
            [datetime(2018, 11, 1, tzinfo=TZ), datetime(2018, 11, 1, tzinfo=TZ)],
        ),
        # Two feeds with expiry dates
        (
            [datetime(2018, 11, 2, tzinfo=TZ), datetime(2018, 11, 1, tzinfo=TZ)],
            [datetime(2018, 11, 1, tzinfo=TZ), datetime(2018, 11, 2, tzinfo=TZ)],
        ),
        # Two feeds, one with an expiry date
        (
            [EMPTY_TIMESTAMP, datetime(2018, 11, 1, tzinfo=TZ)],
            [datetime(2018, 11, 1, tzinfo=TZ), datetime(2018, 11, 1, tzinfo=TZ)],
        ),
    )
    @unpack
    def test_get_first_and_last_expiration_dates(self, expiry_dates, expected):
        # setup

        # test
        results = self.feed_parser.get_first_and_last_expiration_dates(expiry_dates, [])

        # assert
        self.assertEqual(expected[0], results[0])
        self.assertEqual(expected[1], results[1])

    def test_transxchange_extractor_extract(self):
        """This is a re-implementation of the XML file parser class, this is to
        ensure that both the extract method of this class and the XmlFileParser return
        the same result."""
        now = self.xml_file_parser.feed_parser.now
        transxchange_extractor = TransXChangeExtractor(self.file_obj, now)
        extracted = transxchange_extractor.extract()
        file_id = transxchange_extractor.file_id

        services_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "20-1A-A-y08-1",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": EMPTY_TIMESTAMP,
                    "line_names": ["1"],
                    "service_type": "standard",
                },
                {
                    "file_id": file_id,
                    "service_code": "20-2A-A-y08-1",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": datetime(2019, 4, 13, 23, 59, 0, tzinfo=TZ),
                    "line_names": ["2"],
                    "service_type": "standard",
                },
                {
                    "file_id": file_id,
                    "service_code": "20-3A-A-y08-1",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": datetime(2019, 6, 13, 23, 59, 0, tzinfo=TZ),
                    "line_names": ["3"],
                    "service_type": "standard",
                },
            ]
        ).set_index(["file_id", "service_code"])
        self.assertTrue(check_frame_equal(extracted.services, services_expected))
        self.assertCountEqual(
            list(extracted.services.columns),
            ["start_date", "end_date", "line_names", "service_type"],
        )
        self.assertEqual(extracted.services.index.names, ["file_id", "service_code"])

        # assert stop_points - note these are already created by setup()
        stop_points_expected = pd.DataFrame(
            index=(
                obj.atco_code
                for obj in StopPoint.objects.all()
                # .add_district_name()
            )
        )
        stop_points_expected.index.name = "atco_code"

        df1 = (
            extracted.stop_points.drop(columns=["common_name"], axis=1)
            .sort_values("atco_code")
            .reset_index()
        )
        df2 = stop_points_expected.sort_values("atco_code").reset_index()

        self.assertTrue(check_frame_equal(df1, df2))
        self.assertEqual(extracted.stop_points.shape, (11, 1))
        self.assertEqual(extracted.stop_points.shape, (11, 1))
        self.assertCountEqual(list(extracted.stop_points.columns), ["common_name"])
        self.assertEqual(extracted.stop_points.index.names, ["atco_code"])

        # assert routes
        self.assertEqual(extracted.routes.shape, (0, 0))
        self.assertCountEqual(
            list(extracted.routes.columns), []
        )  # routes could be a series
        self.assertEqual(
            extracted.routes.index.names, ["file_id", "route_hash"]
        )  # TODO - rename to route_id

        # assert routes_to_route_links
        self.assertEqual(extracted.route_to_route_links.shape, (0, 1))
        self.assertCountEqual(
            list(extracted.route_to_route_links.columns), ["route_link_ref"]
        )
        self.assertEqual(
            extracted.route_to_route_links.index.names,
            ["file_id", "route_hash", "order"],
        )
        # TODO - rename to route_ref

        # assert route_links
        self.assertEqual(extracted.route_links.shape, (0, 2))
        self.assertCountEqual(
            list(extracted.route_links.columns), ["from_stop_ref", "to_stop_ref"]
        )
        self.assertEqual(
            extracted.route_links.index.names, ["file_id", "route_link_ref"]
        )

        # assert journey_patterns
        self.assertEqual(extracted.journey_patterns.shape[0], 15)
        self.assertCountEqual(
            list(extracted.journey_patterns.columns), ["direction", "service_code"]
        )
        self.assertEqual(
            extracted.journey_patterns.index.names, ["file_id", "journey_pattern_id"]
        )

        # assert jp_to_jps
        self.assertCountEqual(list(extracted.jp_to_jps.columns), ["jp_section_ref"])
        self.assertEqual(
            extracted.jp_to_jps.index.names, ["file_id", "journey_pattern_id", "order"]
        )

        # assert jp_sections
        self.assertCountEqual(list(extracted.jp_sections.columns), [])
        self.assertEqual(
            extracted.jp_sections.index.names, ["file_id", "jp_section_id"]
        )

        # assert timing_links
        self.assertEqual(extracted.timing_links.shape, (20, 12))
        self.assertCountEqual(
            list(extracted.timing_links.columns),
            [
                "jp_section_id",
                "order",
                "from_stop_ref",
                "to_stop_ref",
                "from_activity_id",
                "to_activity_id",
                "route_link_ref",
                "is_timing_status",
                "run_time",
                "wait_time",
                "from_stop_sequence_number",
                "to_stop_sequence_number",
            ],
        )
        self.assertEqual(
            extracted.timing_links.index.names, ["file_id", "jp_timing_link_id"]
        )
        self.assertEqual(
            self.xml_file_parser.feed_parser.now, extracted.import_datetime
        )

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        # assert
        services_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "20-1A-A-y08-1",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": EMPTY_TIMESTAMP,
                    "line_names": ["1"],
                    "service_type": "standard",
                },
                {
                    "file_id": file_id,
                    "service_code": "20-2A-A-y08-1",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": datetime(2019, 4, 13, 23, 59, 0, tzinfo=TZ),
                    "line_names": ["2"],
                    "service_type": "standard",
                },
                {
                    "file_id": file_id,
                    "service_code": "20-3A-A-y08-1",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": datetime(2019, 6, 13, 23, 59, 0, tzinfo=TZ),
                    "line_names": ["3"],
                    "service_type": "standard",
                },
            ]
        ).set_index(["file_id", "service_code"])

        self.assertTrue(check_frame_equal(extracted.services, services_expected))
        self.assertCountEqual(
            list(extracted.services.columns),
            ["start_date", "end_date", "line_names", "service_type"],
        )
        self.assertEqual(extracted.services.index.names, ["file_id", "service_code"])

        # assert stop_points - note these are already created by setup()
        stop_points_expected = pd.DataFrame(
            index=(
                obj.atco_code
                for obj in StopPoint.objects.all()
                # .add_district_name()
            )
        )
        stop_points_expected.index.name = "atco_code"

        df1 = (
            extracted.stop_points.drop(columns=["common_name"], axis=1)
            .sort_values("atco_code")
            .reset_index()
        )
        df2 = stop_points_expected.sort_values("atco_code").reset_index()

        self.assertTrue(check_frame_equal(df1, df2))
        self.assertEqual(extracted.stop_points.shape, (11, 1))
        self.assertEqual(extracted.stop_points.shape, (11, 1))
        self.assertCountEqual(list(extracted.stop_points.columns), ["common_name"])
        self.assertEqual(extracted.stop_points.index.names, ["atco_code"])

        # assert routes
        self.assertEqual(extracted.routes.shape, (0, 0))
        self.assertCountEqual(
            list(extracted.routes.columns), []
        )  # routes could be a series
        self.assertEqual(
            extracted.routes.index.names, ["file_id", "route_hash"]
        )  # TODO - rename to route_id

        # assert routes_to_route_links
        self.assertEqual(extracted.route_to_route_links.shape, (0, 1))
        self.assertCountEqual(
            list(extracted.route_to_route_links.columns), ["route_link_ref"]
        )
        self.assertEqual(
            extracted.route_to_route_links.index.names,
            ["file_id", "route_hash", "order"],
        )
        # TODO - rename to route_ref

        # assert route_links
        self.assertEqual(extracted.route_links.shape, (0, 2))
        self.assertCountEqual(
            list(extracted.route_links.columns), ["from_stop_ref", "to_stop_ref"]
        )
        self.assertEqual(
            extracted.route_links.index.names, ["file_id", "route_link_ref"]
        )

        # assert journey_patterns
        self.assertEqual(extracted.journey_patterns.shape[0], 15)
        self.assertCountEqual(
            list(extracted.journey_patterns.columns), ["direction", "service_code"]
        )
        self.assertEqual(
            extracted.journey_patterns.index.names, ["file_id", "journey_pattern_id"]
        )

        # assert jp_to_jps
        self.assertCountEqual(list(extracted.jp_to_jps.columns), ["jp_section_ref"])
        self.assertEqual(
            extracted.jp_to_jps.index.names, ["file_id", "journey_pattern_id", "order"]
        )

        # assert jp_sections
        self.assertCountEqual(list(extracted.jp_sections.columns), [])
        self.assertEqual(
            extracted.jp_sections.index.names, ["file_id", "jp_section_id"]
        )

        # assert timing_links
        self.assertEqual(extracted.timing_links.shape, (20, 12))
        self.assertCountEqual(
            list(extracted.timing_links.columns),
            [
                "jp_section_id",
                "order",
                "from_stop_ref",
                "to_stop_ref",
                "from_activity_id",
                "to_activity_id",
                "route_link_ref",
                "is_timing_status",
                "run_time",
                "wait_time",
                "from_stop_sequence_number",
                "to_stop_sequence_number",
            ],
        )
        self.assertEqual(
            extracted.timing_links.index.names, ["file_id", "jp_timing_link_id"]
        )

    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id
        Locality.objects.add_district_name()

        # test
        transformed = self.feed_parser.transform(extracted)

        # assert
        # assert services
        services_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "20-1A-A-y08-1",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": EMPTY_TIMESTAMP,
                    "line_names": ["1"],
                    "service_type": "standard",
                },
                {
                    "file_id": file_id,
                    "service_code": "20-2A-A-y08-1",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": datetime(2019, 4, 13, 23, 59, 0, tzinfo=TZ),
                    "line_names": ["2"],
                    "service_type": "standard",
                },
                {
                    "file_id": file_id,
                    "service_code": "20-3A-A-y08-1",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": datetime(2019, 6, 13, 23, 59, 0, tzinfo=TZ),
                    "line_names": ["3"],
                    "service_type": "standard",
                },
            ]
        ).set_index(["file_id", "service_code"])
        self.assertTrue(check_frame_equal(transformed.services, services_expected))
        self.assertCountEqual(
            list(transformed.services.columns),
            ["start_date", "end_date", "line_names", "service_type"],
        )
        self.assertEqual(transformed.services.index.names, ["file_id", "service_code"])

        # assert stop_points - note these are already created by setup()
        stop_points = self.xml_file_parser.create_naptan_stoppoint_df_from_queryset(
            StopPoint.objects.all()
        )
        localities = self.xml_file_parser.create_naptan_locality_df(
            data=(
                {
                    "locality_name": obj.name,
                    "locality_id": obj.gazetteer_id,
                    "admin_area_id": obj.admin_area_id,
                }
                for obj in Locality.objects.all().add_district_name()
            )
        )

        stop_points_expected = stop_points.merge(
            localities, how="left", left_on="locality_id", right_index=True
        )
        stop_points_expected["naptan_id"] = stop_points_expected["naptan_id"].astype(
            object
        )
        self.assertTrue(
            check_frame_equal(transformed.stop_points, stop_points_expected)
        )

        self.assertCountEqual(
            list(transformed.stop_points.columns),
            ["geometry", "naptan_id", "locality_id", "admin_area_id", "locality_name"],
        )
        self.assertEqual(transformed.stop_points.index.names, ["atco_code"])

        self.assertCountEqual(
            list(transformed.service_patterns.columns),
            [
                "direction",
                "service_code",
                "admin_area_codes",
                "geometry",
                "localities",
                "line_name",
                "description",
                "journey_code",
                "vehicle_journey_code",
            ],
        )
        self.assertEqual(
            transformed.service_patterns.index.names, ["file_id", "service_pattern_id"]
        )

        # assert service links
        self.assertEqual(
            transformed.service_links.index.names, ["from_stop_atco", "to_stop_atco"]
        )

        # assert service_pattern_to_service_links
        # self.assertEqual(transformed.service_links.shape, (0, 2))
        self.assertCountEqual(
            list(transformed.service_pattern_to_service_links.columns),
            [
                "from_stop_atco",
                "to_stop_atco",
                "from_activity_id",
                "to_activity_id",
                "file_id",
                "service_pattern_id",
                "journey_pattern_id",
                "vehicle_journey_code",
                "journey_code",
                "order",
                "from_stop_sequence_number",
                "to_stop_sequence_number",
            ],
        )

    # TODO - re-enable this test
    @pytest.mark.skip
    def test_load(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        # test
        result: ETLReport = self.feed_parser.load(transformed)
        revision = self.revision

        # assert

        # assert result
        self.assertEqual(3, result.line_count)
        self.assertEqual(
            datetime(2018, 10, 12, 11, 6, 15, 506200, tzinfo=TZ),
            result.creation_datetime,
        )
        self.assertEqual(
            datetime(2018, 10, 13, 11, 6, 15, 506200, tzinfo=TZ),
            result.modification_datetime,
        )
        self.assertEqual(self.now, result.import_datetime)
        self.assertEqual(
            datetime(2019, 4, 13, tzinfo=TZ), result.first_expiring_service
        )
        self.assertEqual(datetime(2019, 6, 13, tzinfo=TZ), result.last_expiring_service)
        self.assertEqual("", result.bounding_box)

        # assert objects
        self.assertEqual(3, revision.services.count())
        self.assertEqual(12, revision.service_patterns.count())
        self.assertEqual(63, ServicePatternStop.objects.count())

        # Note Localities and AdminArea have not yet been 'rolled up' on the feed at
        # this point but still should have been be created
        admin_areas = (
            AdminArea.objects.filter(
                stops__service_pattern_stops__service_pattern__revision=revision
            )
            .order_by("id")
            .distinct("id")
        )
        self.assertEqual(1, admin_areas.count())

        localities = (
            Locality.objects.filter(
                stops__service_pattern_stops__service_pattern__revision=revision
            )
            .order_by("gazetteer_id")
            .distinct("gazetteer_id")
        )
        self.assertEqual(3, localities.count())

    def test_load_services(self):
        # setup
        file_id = self.trans_xchange_extractor.file_id

        indata = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "20-1A-A-y08-1",
                    "start_date": pd.Timestamp("2018-10-09 00:00:00"),
                    "end_date": pd.Timestamp("2019-04-13 00:00:00"),
                    "line_names": ["1"],
                    "service_type": "standard",
                },
                {
                    "file_id": file_id,
                    "service_code": "20-2A-A-y08-1",
                    "start_date": pd.Timestamp("2018-10-09 00:00:00"),
                    "end_date": pd.Timestamp("2019-04-13 00:00:00"),
                    "line_names": ["2", "2a"],
                    "service_type": "standard",
                },
            ]
        ).set_index("service_code")

        # Test
        actual = self.feed_parser.data_loader.load_services(indata)

        # Assert
        services = Service.objects.all()
        self.assertEqual(services.count(), 2)
        self.assertCountEqual(
            list(actual.columns),
            ["id", "start_date", "end_date", "line_names", "service_type"],
        )

        expected = {
            "20-1A-A-y08-1": {
                "file_id": file_id,
                "service_code": "20-1A-A-y08-1",
                "start_date": date(2018, 10, 9),
                "end_date": date(2019, 4, 13),
                "id": 1,
                "name": "1",
                "other_names": [],
            },
            "20-2A-A-y08-1": {
                "file_id": file_id,
                "service_code": "20-2A-A-y08-1",
                "start_date": date(2018, 10, 9),
                "end_date": date(2019, 4, 13),
                "id": 2,
                "name": "2",
                "other_names": ["2a"],
            },
        }

        for service in services:
            self.assertIsNotNone(service.service_code)
            expected_data = expected[service.service_code]
            self.assertEqual(service.service_code, expected_data["service_code"])
            self.assertEqual(service.start_date, expected_data["start_date"])
            self.assertEqual(service.end_date, expected_data["end_date"])
            self.assertEqual(service.name, expected_data["name"])
            self.assertListEqual(service.other_names, expected_data["other_names"])

    # Service links are not loaded to DB during Indexing
    @skip
    def test_load_service_links(self):
        """The test above using a simplified input failed to catch an error
        when processing a real file.
        Note - route_links are not unique (from_stop_ref, to_stop_ref) pairs, there can
        be multiple route_link_refs with the same stop pair
        """
        # setup
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        # Test
        service_links = self.feed_parser.data_loader.load_service_links(
            transformed.service_links
        )

        # Assert
        self.assertEqual(ServiceLink.objects.count(), 11)
        self.assertCountEqual(
            list(service_links.columns), ["from_stop_id", "to_stop_id", "id"]
        )
        self.assertEqual(service_links.index.names, ["from_stop_atco", "to_stop_atco"])

    def test_load_service_patterns(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        data_loader = self.feed_parser.data_loader
        services = data_loader.load_services(transformed.services)

        # Test
        data_loader.load_service_patterns(
            services,
            transformed.service_patterns,
            transformed.service_pattern_stops,
        )

        # Assert
        revision = self.revision
        self.assertEqual(3, revision.services.count())
        self.assertEqual(12, revision.service_patterns.count())
        self.assertEqual(202, ServicePatternStop.objects.count())

        # Note Localities and AdminArea have not yet been 'rolled up' on the
        # feed at this point but still should have been be created
        admin_areas = (
            AdminArea.objects.filter(
                stops__service_pattern_stops__service_pattern__revision=revision
            )
            .order_by("id")
            .distinct("id")
        )
        self.assertEqual(1, admin_areas.count())

        localities = (
            Locality.objects.filter(
                stops__service_pattern_stops__service_pattern__revision=revision
            )
            .order_by("gazetteer_id")
            .distinct("gazetteer_id")
        )
        self.assertEqual(3, localities.count())


class ExtractTxcNoRoutesTestCase(ExtractBaseTestCase):
    """Test cases around transXchange file with no top level Routes or RouteSections"""

    test_file = "data/NW_01_ANW_2_1.xml"

    # TODO - re-enable this test
    @pytest.mark.skip
    def test_load(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        # test
        result: ETLReport = self.feed_parser.load(transformed)

        # assert

        # Check lines
        self.assertEqual(1, result.line_count)

        # Dates
        self.assertEqual(
            parse("2017-09-21T14:23:13.7546483+01:00"), result.creation_datetime
        )
        self.assertEqual(
            parse("2017-09-21T14:23:13.7546483+01:00"), result.modification_datetime
        )
        self.assertEqual(self.now, result.import_datetime)
        self.assertEqual(
            parse("2099-12-31T00:00:00+00:00"), result.first_expiring_service
        )
        self.assertEqual(
            parse("2099-12-31T00:00:00+00:00"), result.last_expiring_service
        )

        self.assertEqual("", result.bounding_box)


@override_flag("is_timetable_visualiser_active", active=True)
class ExtractUtilitiesTestCase(TestCase):
    """TestCases for utility methods

    Moved such tests here as they don't need to be rerun for different input files
    """

    def test_agg_service_pattern_sequences(self):
        """Test agg_service_pattern_sequences method returns geometry, localities and
        admin_areas sequence for routes"""
        # Setup
        inputs = pd.DataFrame(
            [
                {
                    "file_id": 4288313304800897227,
                    "service_pattern_id": "20-1A-A-y08-1--2245737502598000732",
                    "order": 0,
                    "stop_atco": "0500SBARH011",
                    "naptan_id": 1,
                    "geometry": None,
                    "locality_id": 1,
                    "admin_area_id": 1,
                    "sequence_number": 0,
                },
                {
                    "file_id": 4288313304800897227,
                    "service_pattern_id": "20-1A-A-y08-1--2245737502598000732",
                    "order": 1,
                    "stop_atco": "0500SBARH012",
                    "naptan_id": 2,
                    "geometry": None,
                    "locality_id": 1,
                    "admin_area_id": 1,
                    "sequence_number": 1,
                },
                {
                    "file_id": 4288313304800897227,
                    "service_pattern_id": "20-1A-A-y08-1--2245737502598000732",
                    "order": 2,
                    "stop_atco": "0500SBARH013",
                    "naptan_id": 3,
                    "geometry": None,
                    "locality_id": 1,
                    "admin_area_id": 1,
                    "sequence_number": 2,
                },
            ]
        )

        expected = pd.DataFrame(
            [
                {
                    "file_id": 4288313304800897227,
                    "service_pattern_id": "20-1A-A-y08-1--2245737502598000732",
                    "geometry": None,
                    "localities": [1, 1, 1],
                    "admin_area_codes": [1, 1, 1],
                }
            ]
        ).set_index(["file_id", "service_pattern_id"])

        # Test
        actual = inputs.groupby(["file_id", "service_pattern_id"]).apply(
            agg_service_pattern_sequences
        )

        # Assert
        self.assertTrue(check_frame_equal(actual, expected))


@ddt
@override_flag("is_timetable_visualiser_active", active=True)
class ETLBookingArrangements(ExtractBaseTestCase):
    """Test cases around transXchange file with BookingArrangements data for Flexible Services"""

    test_file = "data/test_extract_booking_arrangements.xml"

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        # assert
        booking_arrangements_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PF0000508:53",
                    "description": "The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm",
                    "tel_national_number": "0345 234 3344",
                    "email": "CallConnect@lincolnshire.gov.uk",
                    "web_address": "https://callconnect.opendrt.co.uk/OpenDRT/",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                extracted.booking_arrangements, booking_arrangements_expected
            )
        )
        self.assertCountEqual(
            list(extracted.booking_arrangements.columns),
            [
                "service_code",
                "description",
                "tel_national_number",
                "email",
                "web_address",
            ],
        )
        self.assertEqual(extracted.booking_arrangements.index.names, ["file_id"])

    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        # test
        transformed = self.feed_parser.transform(extracted)

        # assert services
        booking_arrangements_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PF0000508:53",
                    "description": "The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm",
                    "tel_national_number": "0345 234 3344",
                    "email": "CallConnect@lincolnshire.gov.uk",
                    "web_address": "https://callconnect.opendrt.co.uk/OpenDRT/",
                },
            ]
        ).set_index("file_id")
        self.assertTrue(
            check_frame_equal(
                transformed.booking_arrangements, booking_arrangements_expected
            )
        )
        self.assertCountEqual(
            list(extracted.booking_arrangements.columns),
            [
                "service_code",
                "description",
                "tel_national_number",
                "email",
                "web_address",
            ],
        )

    def test_load(self):
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        # test
        result: ETLReport = self.feed_parser.load(transformed)

        booking_arrangements = BookingArrangements.objects.all()
        service = Service.objects.get(service_code="PF0000508:53")
        service_id = None
        if service:
            service_id = service.id

        self.assertEqual(2, result.line_count)
        self.assertEqual(1, booking_arrangements.count())

        for booking in booking_arrangements:
            self.assertEqual(booking.service_id, service_id)

    @patch("transit_odp.timetables.loaders.get_dataset_adapter_from_revision")
    @patch("transit_odp.transmodel.models.BookingArrangements.objects.bulk_create")
    @patch(
        "transit_odp.pipelines.pipelines.dataset_etl.utils.dataframes.Service.objects.get"
    )
    def test_load_for_same_services_multiple_files(
        self, mock_service_get, mock_bulk_create, mock_get_dataset_adapter
    ):
        logger = MagicMock()
        mock_get_dataset_adapter.return_value = MagicMock(info=logger.info)

        services = pd.DataFrame(
            [
                {
                    "file_id": 112,
                    "service_code": "PF0000508:53",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": EMPTY_TIMESTAMP,
                    "line_names": ["1"],
                    "service_type": "flexible",
                    "id": 1,
                },
                {
                    "file_id": 113,
                    "service_code": "PF0000508:53",
                    "start_date": datetime(2018, 10, 9, tzinfo=TZ),
                    "end_date": EMPTY_TIMESTAMP,
                    "line_names": ["1"],
                    "service_type": "flexible",
                    "id": 2,
                },
            ]
        ).set_index(["file_id", "service_code"])

        booking_arrangements = pd.DataFrame(
            [
                {
                    "file_id": 112,
                    "service_code": "PF0000508:53",
                    "description": "The booking office is open",
                    "tel_national_number": "0345 234 3344",
                    "email": "CallConnect@lincolnshire.gov.uk",
                    "web_address": "https://callconnect.opendrt.co.uk/OpenDRT",
                },
                {
                    "file_id": 113,
                    "service_code": "PF0000508:53",
                    "description": "The booking office is open",
                    "tel_national_number": "0345 234 3344",
                    "email": "CallConnect@lincolnshire.gov.uk",
                    "web_address": "https://callconnect.opendrt.co.uk/OpenDRT",
                },
            ]
        )

        service_patterns = pd.DataFrame()
        service_pattern_to_service_links = pd.DataFrame()
        service_links = pd.DataFrame()
        stop_points = pd.DataFrame()
        service_pattern_stops = pd.DataFrame()
        schema_version = ""
        creation_datetime = ""
        modification_datetime = ""
        import_datetime = ""
        line_count = ""
        line_names = ""
        stop_count = ""
        most_common_localities = ""
        timing_point_count = ""
        vehicle_journeys = pd.DataFrame()
        serviced_organisations = pd.DataFrame()
        flexible_operation_periods = pd.DataFrame()
        operating_profiles = pd.DataFrame()

        transformed = TransformedData(
            services=services,
            service_patterns=service_patterns,
            service_pattern_to_service_links=service_pattern_to_service_links,
            service_links=service_links,
            stop_points=stop_points,
            service_pattern_stops=service_pattern_stops,
            booking_arrangements=booking_arrangements,
            schema_version=schema_version,
            creation_datetime=creation_datetime,
            modification_datetime=modification_datetime,
            import_datetime=import_datetime,
            line_count=line_count,
            line_names=line_names,
            stop_count=stop_count,
            most_common_localities=most_common_localities,
            timing_point_count=timing_point_count,
            vehicle_journeys=vehicle_journeys,
            serviced_organisations=serviced_organisations,
            flexible_operation_periods=flexible_operation_periods,
            operating_profiles=operating_profiles,
        )

        service_cache = []
        service_link_cache = []

        revision = DatasetRevision(id=1)

        mock_service_get.side_effect = [ServiceFactory(), ServiceFactory()]

        mock_bulk_create.return_value = [MagicMock(id=1), MagicMock(id=2)]

        data_loader = TransXChangeDataLoader(
            transformed, service_cache, service_link_cache
        )
        result_df = data_loader.load_booking_arrangements(services, revision)

        booking_arrangements = BookingArrangements.objects.all()

        self.assertEqual(2, result_df.shape[0])

        self.assertListEqual([1, 2], result_df.index.get_level_values("id").tolist())


@ddt
class ETLBookingArrangementsWithMinimumElements(ExtractBaseTestCase):
    """Test cases around transXchange file with BookingArrangements data for Flexible Services"""

    test_file = "data/test_extract_booking_arrangements_with_minimum_elements.xml"

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        # assert
        booking_arrangements_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PF0000508:53",
                    "description": "The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm",
                    "tel_national_number": "0345 234 3344",
                },
                {
                    "file_id": file_id,
                    "service_code": "PF0000508:53",
                    "description": "The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm",
                    "email": "CallConnect@lincolnshire.gov.uk",
                },
                {
                    "file_id": file_id,
                    "service_code": "PF0000508:53",
                    "description": "The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm",
                    "web_address": "https://callconnect.opendrt.co.uk/OpenDRT/",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                extracted.booking_arrangements, booking_arrangements_expected
            )
        )
        self.assertCountEqual(
            list(extracted.booking_arrangements.columns),
            [
                "service_code",
                "description",
                "tel_national_number",
                "email",
                "web_address",
            ],
        )
        self.assertEqual(extracted.booking_arrangements.index.names, ["file_id"])

    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        file_id = self.trans_xchange_extractor.file_id

        # test
        transformed = self.feed_parser.transform(extracted)

        # assert services
        booking_arrangements_expected = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PF0000508:53",
                    "description": "The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm",
                    "tel_national_number": "0345 234 3344",
                },
                {
                    "file_id": file_id,
                    "service_code": "PF0000508:53",
                    "description": "The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm",
                    "email": "CallConnect@lincolnshire.gov.uk",
                },
                {
                    "file_id": file_id,
                    "service_code": "PF0000508:53",
                    "description": "The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm",
                    "web_address": "https://callconnect.opendrt.co.uk/OpenDRT/",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                transformed.booking_arrangements, booking_arrangements_expected
            )
        )
        self.assertCountEqual(
            list(extracted.booking_arrangements.columns),
            [
                "service_code",
                "description",
                "tel_national_number",
                "email",
                "web_address",
            ],
        )

    def test_load(self):
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        # test
        result: ETLReport = self.feed_parser.load(transformed)

        booking_arrangements = BookingArrangements.objects.all()
        service = Service.objects.get(service_code="PF0000508:53")
        service_id = None
        if service:
            service_id = service.id

        self.assertEqual(2, result.line_count)
        self.assertEqual(3, booking_arrangements.count())

        for booking in booking_arrangements:
            self.assertEqual(booking.service_id, service_id)
