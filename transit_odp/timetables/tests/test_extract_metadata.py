import os
from datetime import datetime
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


from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.naptan.models import AdminArea, District, Locality, StopPoint
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.timetables.extract import TransXChangeExtractor

from transit_odp.xmltoolkit.xml_toolkit import XmlToolkit

TZ = tz.gettz("Europe/London")
EMPTY_TIMESTAMP = None


class ExtractBaseTestCase(TestCase):
    test_file: str

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
        self.now = datetime.now()
        xml_toolkit = XmlToolkit({"x": "http://www.transxchange.org.uk/"})

        # Test file
        self.file_obj = File(os.path.join(self.cur_dir, self.test_file))
        self.doc, result = xml_toolkit.parse_xml_file(self.file_obj.file)

        # FeedParser performs the metadata extraction
        feed_progress = DatasetETLTaskResultFactory(revision=self.revision)
        self.trans_xchange_extractor = TransXChangeExtractor(self.file_obj, self.now)

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
            common_name = xml_toolkit.get_child_text(xml_stoppointref, "x:CommonName")
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
