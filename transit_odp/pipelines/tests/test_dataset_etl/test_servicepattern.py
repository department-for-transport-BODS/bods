import datetime
import os

import pandas as pd
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
        df_stop_sequence = df_expected[["atco_code"]]

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
