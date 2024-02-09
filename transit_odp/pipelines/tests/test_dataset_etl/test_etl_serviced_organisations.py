from dateutil import tz
import pandas as pd

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.transmodel.factories import ServicedOrganisationsFactory
from transit_odp.transmodel.models import (
    ServicedOrganisationWorkingDays,
    ServicedOrganisations,
)
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
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "start_date": "2022-06-05",
                    "end_date": "2022-07-26",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "start_date": "2022-09-04",
                    "end_date": "2022-10-21",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "start_date": "2022-10-30",
                    "end_date": "2022-12-16",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "start_date": "2023-01-03",
                    "end_date": "2023-02-10",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "start_date": "2023-02-19",
                    "end_date": "2023-03-31",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "start_date": "2023-04-16",
                    "end_date": "2023-05-26",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "start_date": "2023-06-04",
                    "end_date": "2023-07-25",
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

    def test_transform(self):
        # setup
        file_id = hash(self.file_obj.file)
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        expected_serviced_organisation = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": True,
                    "start_date": "2022-06-05",
                    "end_date": "2022-07-26",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCCSC",
                    "name": "NYCC Schools",
                    "operational": False,
                    "start_date": "2022-06-05",
                    "end_date": "2022-07-26",
                },
            ]
        ).set_index("file_id")

        self.assertEqual(14, transformed.serviced_organisations.shape[0])

        self.assertCountEqual(
            list(transformed.serviced_organisations.columns),
            expected_serviced_organisation.columns,
        )

    def test_load(self):
        # setup
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        serviced_orgs = ServicedOrganisations.objects.all()
        serviced_org_working_days = ServicedOrganisationWorkingDays.objects.all()
        # test
        self.assertEqual(1, serviced_orgs.count())
        self.assertEqual(7, serviced_org_working_days.count())
        for serviced_org in serviced_orgs:
            self.assertEqual(serviced_org.name, "NYCC Schools")


@override_flag("is_timetable_visualiser_active", active=True)
class ETLServicedOrganisationsWithOrgInDB(ExtractBaseTestCase):
    test_file = "data/test_serviced_organisations/test_extract_serviced_organisations_for_org_in_db.xml"

    def test_load(self):
        # setup
        ServicedOrganisationsFactory(organisation_code="TSTCODE")
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        serviced_orgs = ServicedOrganisations.objects.all()
        serviced_org_working_days = ServicedOrganisationWorkingDays.objects.all()
        # test
        self.assertEqual(2, serviced_orgs.count())
        self.assertEqual(14, serviced_org_working_days.count())
