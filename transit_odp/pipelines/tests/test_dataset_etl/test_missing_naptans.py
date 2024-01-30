import datetime
import os
from unittest import skip

from django.core.files import File
from django.test import TestCase

from transit_odp.naptan.factories import (
    AdminAreaFactory,
    DistrictFactory,
    LocalityFactory,
)
from transit_odp.naptan.models import StopPoint
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


class MissingNaptansTestCase(TestCase):
    # Tests that when all naptan stops are missing, the feed goes to error.
    # But if just one naptan stop is present, the feed is allowed to go live with
    # minor errors.

    def setUp(self):
        self.now = datetime.datetime.now()

        self.cur_dir = os.path.abspath(os.path.dirname(__file__))
        self.org = OrganisationFactory()
        self.admin_area = AdminAreaFactory()
        self.district = DistrictFactory()
        self.locality = LocalityFactory(
            district=self.district, admin_area=self.admin_area
        )

    # Tests that the feed goes to error if all naptan stops are missing.
    @skip
    def test_all_naptan_stops_missing(self):
        # setup
        file = os.path.join(self.cur_dir, "data/test_servicepattern/test.xml")

        revision = DatasetRevisionFactory(
            dataset__organisation=self.org,
            is_published=False,
            status=FeedStatus.pending.value,
        )

        feed_progress = DatasetETLTaskResultFactory.create(revision=revision)

        self.feed_parser = FeedParser(revision, None, feed_progress)

        # We need naptan localities and stops
        create_naptan_localities(
            self.feed_parser,
            File(file, name="test_file"),
            self.admin_area,
            self.district,
        )

        # No stops in this test
        revision.associate_file(file)

        # test
        self.feed_parser.index_feed()

        # assert
        self.assertEqual(FeedStatus.error.value, revision.status)
        self.assertEqual(
            "The feed does not reference any valid Naptan codes.",
            revision.errors.all()[0].description,
        )

    # Tests that the feed goes live if all but one naptan stops are missing.
    @skip
    def test_all_but_one_naptan_stops_missing(self):
        # setup
        file = os.path.join(self.cur_dir, "data/test_servicepattern/test.xml")

        revision = DatasetRevisionFactory(
            dataset__organisation=self.org,
            is_published=False,
            status=FeedStatus.pending.value,
        )

        feed_progress = DatasetETLTaskResultFactory.create(revision=revision)

        self.feed_parser = FeedParser(revision, None, feed_progress)

        # We need naptan localities and stops
        localities = create_naptan_localities(
            self.feed_parser,
            File(file, name="test_file"),
            self.admin_area,
            self.district,
        )

        # Create then delete all but one naptan stops
        create_naptan_stops(
            self.feed_parser, File(file, name="test_file"), localities, self.admin_area
        )
        stops = StopPoint.objects.all()
        for index, stop in enumerate(stops):
            if index != 0:
                stop.delete()

        self.assertEqual(1, StopPoint.objects.all().count())

        revision.associate_file(file)

        # test
        self.feed_parser.index_feed()

        # assert
