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
    ServicedOrganisationVehicleJourney,
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


@override_flag("is_timetable_visualiser_active", active=True)
class ETLServicedOrganisationsWithMultipleServicedOrfRefs(ExtractBaseTestCase):
    test_file = "data/test_serviced_organisations/test_extract_serviced_organisations_for_multiple_refs.xml"

    def test_extract(self):
        # setup
        file_id = hash(self.file_obj.file)

        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        expected_serviced_organisation = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "start_date": "2023-01-04",
                    "end_date": "2023-02-10",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "start_date": "2023-02-20",
                    "end_date": "2023-03-31",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "start_date": "2023-02-20",
                    "end_date": "2023-03-31",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "start_date": "2023-04-17",
                    "end_date": "2023-05-26",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "start_date": "2023-06-05",
                    "end_date": "2023-07-21",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "start_date": "2023-09-05",
                    "end_date": "2023-10-27",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "start_date": "2023-11-06",
                    "end_date": "2023-12-22",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NY2024",
                    "name": "North Yorkshire 2024",
                    "start_date": "2024-01-08",
                    "end_date": "2024-02-09",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NY2024",
                    "name": "North Yorkshire 2024",
                    "start_date": "2024-02-19",
                    "end_date": "2024-03-22",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NY2024",
                    "name": "North Yorkshire 2024",
                    "start_date": "2024-04-08",
                    "end_date": "2024-05-24",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NY2024",
                    "name": "North Yorkshire 2024",
                    "start_date": "2024-06-03",
                    "end_date": "2024-07-19",
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
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "operational": True,
                    "start_date": "2023-01-04",
                    "end_date": "2023-02-10",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "operational": True,
                    "start_date": "2023-02-20",
                    "end_date": "2023-03-31",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "operational": True,
                    "start_date": "2023-04-17",
                    "end_date": "2023-05-26",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "operational": True,
                    "start_date": "2023-06-05",
                    "end_date": "2023-07-21",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "operational": True,
                    "start_date": "2023-09-05",
                    "end_date": "2023-10-27",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NYCC2023:2",
                    "name": "North Yorkshire 2023",
                    "operational": True,
                    "start_date": "2023-11-06",
                    "end_date": "2023-12-22",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NY2024",
                    "name": "North Yorkshire 2024",
                    "operational": True,
                    "start_date": "2024-01-08",
                    "end_date": "2024-02-09",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NY2024",
                    "name": "North Yorkshire 2024",
                    "operational": True,
                    "start_date": "2024-02-19",
                    "end_date": "2024-03-22",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NY2024",
                    "name": "North Yorkshire 2024",
                    "operational": True,
                    "start_date": "2024-04-08",
                    "end_date": "2024-05-24",
                },
                {
                    "file_id": file_id,
                    "serviced_org_ref": "NY2024",
                    "name": "North Yorkshire 2024",
                    "operational": True,
                    "start_date": "2024-06-03",
                    "end_date": "2024-07-19",
                },
            ]
        ).set_index("file_id")

        self.assertEqual(10, transformed.serviced_organisations.shape[0])

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
        self.assertEqual(2, serviced_orgs.count())
        self.assertEqual(10, serviced_org_working_days.count())

        serviced_org_names = {serviced_org.name for serviced_org in serviced_orgs}

        self.assertIn("North Yorkshire 2023", serviced_org_names)

        self.assertIn("North Yorkshire 2024", serviced_org_names)


@override_flag("is_timetable_visualiser_active", active=True)
class ETLServicedOrganisationsServicesVehicleJourney(ExtractBaseTestCase):
    test_file = "data/test_serviced_orgs_vehicle_journeys_junction/test_load_serviced_orgs_vjs_junction.xml"

    def test_load_operating_profiles_in_services(self):
        # setup
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        serviced_orgs_vehicle_journeys = (
            ServicedOrganisationVehicleJourney.objects.all()
        )

        # test
        self.assertEqual(2, serviced_orgs_vehicle_journeys.count())


@override_flag("is_timetable_visualiser_active", active=True)
class ETLServicedOrganisationsServicesVehicleJourney(ExtractBaseTestCase):
    test_file = (
        "data/test_serviced_organisations/test_extract_serviced_organisations.xml"
    )

    def test_load_operating_profiles_in_vehicle_journeys(self):
        # setup
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        serviced_orgs_vehicle_journeys = (
            ServicedOrganisationVehicleJourney.objects.all()
        )

        # test
        self.assertEqual(40, serviced_orgs_vehicle_journeys.count())
