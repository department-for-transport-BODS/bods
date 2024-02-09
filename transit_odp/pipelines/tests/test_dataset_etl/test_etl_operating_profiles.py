from dateutil import tz
import pandas as pd

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.transmodel.models import OperatingProfile
from waffle.testutils import override_flag

TZ = tz.gettz("Europe/London")


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingProfilesServices(ExtractBaseTestCase):
    test_file = "data/test_operating_profiles/test_operating_profiles_services.xml"

    def test_extract(self):
        # setup
        file_id = hash(self.file_obj.file)

        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        expected_operating_profiles = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3681",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Tuesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3681",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Wednesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3681",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Thursday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3681",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Friday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3682",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Tuesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3682",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Wednesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3682",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Thursday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3682",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Friday",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(extracted.operating_profiles, expected_operating_profiles)
        )

        self.assertCountEqual(
            list(extracted.operating_profiles.columns),
            list(expected_operating_profiles.columns),
        )
        self.assertEqual(extracted.operating_profiles.index.names, ["file_id"])

    def test_transform(self):
        # setup
        file_id = hash(self.file_obj.file)
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        expected_operating_profiles = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3681",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Tuesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3681",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Wednesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3681",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Thursday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3681",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Friday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3682",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Tuesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3682",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Wednesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3682",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Thursday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0000582:186",
                    "vehicle_journey_code": "3682",
                    "serviced_org_ref": "Sch:11",
                    "operational": True,
                    "days_of_week": "Friday",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                transformed.operating_profiles, expected_operating_profiles
            )
        )

        self.assertCountEqual(
            list(transformed.operating_profiles.columns),
            list(expected_operating_profiles.columns),
        )

    def test_load(self):
        # setup
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        operating_profiles = OperatingProfile.objects.all()
        # test

        self.assertEqual(8, operating_profiles.count())


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingProfilesVehicleJourneys(ExtractBaseTestCase):
    test_file = (
        "data/test_operating_profiles/test_operating_profiles_vehicle_journeys.xml"
    )

    def test_extract(self):
        # setup
        file_id = hash(self.file_obj.file)

        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        expected_operating_profiles = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ4",
                    "serviced_org_ref": "NYCCSC",
                    "operational": True,
                    "days_of_week": "Monday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ4",
                    "serviced_org_ref": "NYCCSC",
                    "operational": True,
                    "days_of_week": "Tuesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ4",
                    "serviced_org_ref": "NYCCSC",
                    "operational": True,
                    "days_of_week": "Wednesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ4",
                    "serviced_org_ref": "NYCCSC",
                    "operational": True,
                    "days_of_week": "Thursday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ4",
                    "serviced_org_ref": "NYCCSC",
                    "operational": True,
                    "days_of_week": "Friday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ12",
                    "serviced_org_ref": "NYCCSC",
                    "operational": False,
                    "days_of_week": "Monday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ12",
                    "serviced_org_ref": "NYCCSC",
                    "operational": False,
                    "days_of_week": "Tuesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ12",
                    "serviced_org_ref": "NYCCSC",
                    "operational": False,
                    "days_of_week": "Wednesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ12",
                    "serviced_org_ref": "NYCCSC",
                    "operational": False,
                    "days_of_week": "Thursday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ12",
                    "serviced_org_ref": "NYCCSC",
                    "operational": False,
                    "days_of_week": "Friday",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(extracted.operating_profiles, expected_operating_profiles)
        )

        self.assertCountEqual(
            list(extracted.operating_profiles.columns),
            list(expected_operating_profiles.columns),
        )
        self.assertEqual(extracted.operating_profiles.index.names, ["file_id"])

    def test_transform(self):
        # setup
        file_id = hash(self.file_obj.file)
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        expected_operating_profiles = pd.DataFrame(
            [
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ4",
                    "serviced_org_ref": "NYCCSC",
                    "operational": True,
                    "days_of_week": "Monday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ4",
                    "serviced_org_ref": "NYCCSC",
                    "operational": True,
                    "days_of_week": "Tuesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ4",
                    "serviced_org_ref": "NYCCSC",
                    "operational": True,
                    "days_of_week": "Wednesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ4",
                    "serviced_org_ref": "NYCCSC",
                    "operational": True,
                    "days_of_week": "Thursday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ4",
                    "serviced_org_ref": "NYCCSC",
                    "operational": True,
                    "days_of_week": "Friday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ12",
                    "serviced_org_ref": "NYCCSC",
                    "operational": False,
                    "days_of_week": "Monday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ12",
                    "serviced_org_ref": "NYCCSC",
                    "operational": False,
                    "days_of_week": "Tuesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ12",
                    "serviced_org_ref": "NYCCSC",
                    "operational": False,
                    "days_of_week": "Wednesday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ12",
                    "serviced_org_ref": "NYCCSC",
                    "operational": False,
                    "days_of_week": "Thursday",
                },
                {
                    "file_id": file_id,
                    "service_code": "PB0001746:15",
                    "vehicle_journey_code": "VJ12",
                    "serviced_org_ref": "NYCCSC",
                    "operational": False,
                    "days_of_week": "Friday",
                },
            ]
        ).set_index("file_id")

        self.assertTrue(
            check_frame_equal(
                transformed.operating_profiles, expected_operating_profiles
            )
        )

        self.assertCountEqual(
            list(transformed.operating_profiles.columns),
            list(expected_operating_profiles.columns),
        )

    def test_load(self):
        # setup
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        operating_profiles = OperatingProfile.objects.all()
        # test

        self.assertEqual(10, operating_profiles.count())
