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
from transit_odp.transmodel.models import ServicePatternStop


class ZipFileWithDirectoriesTestCase(TestCase):
    # Tests indexing of a zip containing hierarchical directories/files

    def setUp(self):
        self.now = datetime.datetime.now()
        self.cur_dir = os.path.abspath(os.path.dirname(__file__))
        self.org = OrganisationFactory()
        self.admin_area = AdminAreaFactory()
        self.district = DistrictFactory()
        self.locality = LocalityFactory(
            district=self.district, admin_area=self.admin_area
        )

    def test_zipfile_with_directories(self):
        # setup

        # zipfile_with_directories.zip contains the same files as EA_TXC_5_files.zip,
        # but just within
        # multiple nested directories. So we should have the same outcome as the
        # test_index_optimisation test.

        file = os.path.join(self.cur_dir, "data/zipfile_with_directories.zip")

        revision = DatasetRevisionFactory(
            dataset__organisation=self.org,
            is_published=False,
            status=FeedStatus.pending.value,
        )

        revision.associate_file(file)

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

        self.feed_parser.index_feed()

        self.assertEqual(3, revision.num_of_lines)
        self.assertEqual(
            "2099-04-13T23:59:00+00:00", revision.first_expiring_service.isoformat()
        )
        self.assertEqual(
            "2099-04-13T23:59:00+00:00", revision.last_expiring_service.isoformat()
        )
        self.assertEqual("2.1", revision.transxchange_version)

        self.assertEqual(1, revision.admin_areas.count())
        self.assertEqual(3, revision.services.count())
        self.assertEqual(3, revision.localities.count())
        self.assertEqual(4, revision.service_patterns.count())
        self.assertEqual(
            21,
            ServicePatternStop.objects.filter(
                service_pattern__revision=revision
            ).count(),
        )
