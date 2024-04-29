import datetime
import os

from django.core.files import File
from django.test import TestCase

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
from transit_odp.timetables.etl import TransXChangePipeline
from transit_odp.transmodel.models import ServicePatternStop


class IndexOptimisationTestCase(TestCase):
    # Tests setup to verify correct behaviour before refactoring / improvements made.

    def setUp(self):
        self.now = datetime.datetime.now()

        self.cur_dir = os.path.abspath(os.path.dirname(__file__))
        self.org = OrganisationFactory()
        self.admin_area = AdminAreaFactory()
        self.district = DistrictFactory()
        self.locality = LocalityFactory(
            district=self.district, admin_area=self.admin_area
        )

    def test_overall_indexing_zip_single_file(self):
        # setup
        file = os.path.join(self.cur_dir, "data/EA_TXC_5_files.zip")

        revision = DatasetRevisionFactory(
            is_published=False, status=FeedStatus.pending.value
        )

        revision.associate_file(file)
        revision.save()

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

        # test
        self.feed_parser.index_feed()

        # assert

        # return

        self.assertEqual(1, revision.num_of_lines)
        self.assertEqual(
            "2099-04-13T23:59:00+00:00", revision.first_expiring_service.isoformat()
        )
        self.assertEqual(
            "2099-04-13T23:59:00+00:00", revision.last_expiring_service.isoformat()
        )
        self.assertEqual("2.1", revision.transxchange_version)

        self.assertEqual(1, revision.admin_areas.count())
        self.assertEqual(1, revision.services.count())
        self.assertEqual(3, revision.localities.count())
        self.assertEqual(4, revision.service_patterns.count())
        self.assertEqual(
            21,
            ServicePatternStop.objects.filter(
                service_pattern__revision=revision
            ).count(),
        )

    def test_overall_indexing_zip_multiple_files(self):
        # setup
        file = os.path.join(self.cur_dir, "data/2lines.zip")

        revision = DatasetRevisionFactory(
            is_published=False, status=FeedStatus.pending.value
        )

        revision.associate_file(file)
        revision.save()

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

        # test
        self.feed_parser.index_feed()

        # assert

        # return

        self.assertEqual(2, revision.num_of_lines)
        self.assertEqual(
            "2099-04-13T23:59:00+00:00", revision.first_expiring_service.isoformat()
        )
        self.assertEqual(
            "2099-04-13T23:59:00+00:00", revision.last_expiring_service.isoformat()
        )
        self.assertEqual("2.1", revision.transxchange_version)

        self.assertEqual(1, revision.admin_areas.count())
        self.assertEqual(2, revision.services.count())
        self.assertEqual(3, revision.localities.count())
        self.assertEqual(8, revision.service_patterns.count())
        self.assertEqual(
            42,
            ServicePatternStop.objects.filter(
                service_pattern__revision=revision
            ).count(),
        )

    def test_overall_indexing_zip_multiple_files_transxchangeparser(self):
        # setup
        file = os.path.join(self.cur_dir, "data/2lines.zip")

        revision = DatasetRevisionFactory(
            is_published=False, status=FeedStatus.pending.value
        )

        revision.associate_file(file)
        revision.save()

        feed_progress = DatasetETLTaskResultFactory.create(revision=revision)
        self.feed_parser = FeedParser(revision, feed_progress)
        self.pipeline = TransXChangePipeline(revision)

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

        self.pipeline.run()

        self.assertEqual(2, revision.num_of_lines)
        self.assertEqual(
            "2099-04-13T23:59:00+00:00", revision.first_expiring_service.isoformat()
        )
        self.assertEqual(
            "2099-04-13T23:59:00+00:00", revision.last_expiring_service.isoformat()
        )
        self.assertEqual("2.1", revision.transxchange_version)

        self.assertEqual(1, revision.admin_areas.count())
        self.assertEqual(2, revision.services.count())
        self.assertEqual(3, revision.localities.count())
        self.assertEqual(8, revision.service_patterns.count())
        self.assertEqual(
            42,
            ServicePatternStop.objects.filter(
                service_pattern__revision=revision
            ).count(),
        )

    def test_overall_indexing_xml_transxchangeparser(self):
        file = os.path.join(self.cur_dir, "data/NW_01_ANW_2_1.xml")
        revision = DatasetRevisionFactory(
            is_published=False, status=FeedStatus.pending.value
        )

        revision.associate_file(file)
        revision.save()

        feed_progress = DatasetETLTaskResultFactory.create(revision=revision)
        # This is only used to create the naptan localities
        self.feed_parser = FeedParser(revision, feed_progress)
        self.pipeline = TransXChangePipeline(revision)

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

        self.pipeline.run()
        self.assertEqual(1, revision.num_of_lines)
        self.assertEqual(
            "2099-12-31T23:59:00+00:00", revision.first_expiring_service.isoformat()
        )
        self.assertEqual(
            "2099-12-31T23:59:00+00:00", revision.last_expiring_service.isoformat()
        )
        self.assertEqual("2.1", revision.transxchange_version)

        self.assertEqual(1, revision.admin_areas.count())
        self.assertEqual(1, revision.services.count())
        self.assertEqual(
            25,
            ServicePatternStop.objects.filter(
                service_pattern__revision=revision
            ).count(),
        )

    def test_overall_indexing_xml(self):
        # setup
        file = os.path.join(self.cur_dir, "data/NW_01_ANW_2_1.xml")

        revision = DatasetRevisionFactory(
            is_published=False, status=FeedStatus.pending.value
        )

        revision.associate_file(file)
        revision.save()

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

        # test
        self.feed_parser.index_feed()

        # assert

        # return

        self.assertEqual(1, revision.num_of_lines)
        self.assertEqual(
            "2099-12-31T23:59:00+00:00", revision.first_expiring_service.isoformat()
        )
        self.assertEqual(
            "2099-12-31T23:59:00+00:00", revision.last_expiring_service.isoformat()
        )
        self.assertEqual("2.1", revision.transxchange_version)

        self.assertEqual(1, revision.admin_areas.count())
        self.assertEqual(1, revision.services.count())
        self.assertEqual(
            25,
            ServicePatternStop.objects.filter(
                service_pattern__revision=revision
            ).count(),
        )

    def test_non_naptan_xml_file_transxchange_parser(self):
        # setup
        filepath = os.path.join(self.cur_dir, "data/x.xml")

        with open(filepath, "r") as fin:
            revision = DatasetRevisionFactory(
                is_published=False,
                status=FeedStatus.pending.value,
                upload_file__from_file=fin,
            )

        DatasetETLTaskResultFactory.create(revision=revision)
        self.pipeline = TransXChangePipeline(revision)

        # We need naptan districts and localities
        district = DistrictFactory.create(name="District1")
        admin_area = AdminAreaFactory.create(atco_code="553")
        LocalityFactory.create(
            gazetteer_id="E0039203",
            name="",
            district=district,
            admin_area=admin_area,
        )

        self.pipeline.run()

        self.assertEqual(2, revision.num_of_lines)
        self.assertEqual(
            "2024-09-13T23:59:00+01:00", revision.first_expiring_service.isoformat()
        )
        self.assertEqual(
            "2024-09-13T23:59:00+01:00", revision.last_expiring_service.isoformat()
        )
        self.assertEqual("2.4", revision.transxchange_version)

        self.assertEqual(1, revision.admin_areas.count())
        self.assertEqual(1, revision.services.count())
        self.assertEqual(1, revision.localities.count())
        self.assertEqual(2, revision.service_patterns.count())
        self.assertEqual(
            10,
            ServicePatternStop.objects.filter(
                service_pattern__revision=revision
            ).count(),
        )
        first_start_str = revision.first_service_start.strftime("%Y%m%d")
        org_name = revision.dataset.organisation.name
        expected_revision_name = f"{org_name}_unknown_unknown_{first_start_str}"
        self.assertEqual(revision.name, expected_revision_name)

    def test_non_naptan_xml_file(self):
        # setup
        filepath = os.path.join(self.cur_dir, "data/x.xml")

        with open(filepath, "r") as fin:
            revision = DatasetRevisionFactory(
                is_published=False,
                status=FeedStatus.pending.value,
                upload_file__from_file=fin,
            )

        feed_progress = DatasetETLTaskResultFactory.create(revision=revision)
        self.feed_parser = FeedParser(revision, feed_progress)

        # We need naptan districts and localities
        district = DistrictFactory.create(name="District1")
        admin_area = AdminAreaFactory.create(atco_code="553")
        LocalityFactory.create(
            gazetteer_id="E0039203",
            name="",
            district=district,
            admin_area=admin_area,
        )

        # test
        self.feed_parser.index_feed()

        # assert

        # return

        self.assertEqual(2, revision.num_of_lines)
        self.assertEqual(
            "2024-09-13T23:59:00+01:00", revision.first_expiring_service.isoformat()
        )
        self.assertEqual(
            "2024-09-13T23:59:00+01:00", revision.last_expiring_service.isoformat()
        )
        self.assertEqual("2.4", revision.transxchange_version)

        self.assertEqual(1, revision.admin_areas.count())
        self.assertEqual(1, revision.services.count())
        self.assertEqual(1, revision.localities.count())
        self.assertEqual(2, revision.service_patterns.count())
        self.assertEqual(
            10,
            ServicePatternStop.objects.filter(
                service_pattern__revision=revision
            ).count(),
        )
        first_start_str = revision.first_service_start.strftime("%Y%m%d")
        org_name = revision.dataset.organisation.name
        expected_revision_name = f"{org_name}_unknown_unknown_{first_start_str}"
        self.assertEqual(revision.name, expected_revision_name)
