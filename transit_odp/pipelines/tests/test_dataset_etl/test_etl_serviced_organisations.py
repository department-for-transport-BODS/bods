from dateutil import tz
import pandas as pd

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.transmodel.models import ServicedOrganisations
from waffle.testutils import override_flag

TZ = tz.gettz("Europe/London")


@override_flag("is_timetable_visualiser_active", active=True)
class ETLServicedOrganisations(ExtractBaseTestCase):
    test_file = (
        "data/test_serviced_organisations/test_extract_serviced_organisations.xml"
    )

    def test_extract(self):
        # setup
        file_id = hash(self.file_obj.file)

        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        expected_serviced_organisation = pd.DataFrame(
            [
                {
                    "file_id": self.xml_file_parser.file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                extracted.serviced_organisations, expected_serviced_organisation
            )
        )

        self.assertCountEqual(
            list(extracted.serviced_organisations.columns),
            list(expected_serviced_organisation.columns),
        )
        self.assertEqual(extracted.serviced_organisations.index.names, ["file_id"])

    def test_transform(self):
        # setup
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        file_id = self.xml_file_parser.file_id

        # test
        transformed = self.feed_parser.transform(extracted)

        expected_serviced_organisation = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                transformed.serviced_organisations, expected_serviced_organisation
            )
        )

        self.assertCountEqual(
            list(transformed.serviced_organisations.columns),
            list(expected_serviced_organisation.columns),
        )

    def test_load(self):
        # setup
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        serviced_orgs = ServicedOrganisations.objects.all()
        # test

        self.assertEqual(1, serviced_orgs.count())
        for serviced_org in serviced_orgs:
            self.assertEqual(serviced_org.name, "NYCC Schools")
