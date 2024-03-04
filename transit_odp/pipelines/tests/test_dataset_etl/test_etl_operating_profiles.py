from dateutil import tz
from transit_odp.pipelines.tests.test_dataset_etl.test_etl_operating_dates_exceptions import (
    setup_bank_holidays,
)

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.transmodel.models import OperatingProfile
from waffle.testutils import override_flag

TZ = tz.gettz("Europe/London")

columns = [
    "service_code",
    "vehicle_journey_code",
    "serviced_org_ref",
    "operational",
    "day_of_week",
    "exceptions_operational",
    "exceptions_date",
]


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingProfilesServices(ExtractBaseTestCase):
    test_file = "data/test_operating_profiles/test_operating_profiles_services.xml"

    def test_extract(self):
        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        self.assertEqual(extracted.operating_profiles.shape[0], 8)

        self.assertCountEqual(
            list(extracted.operating_profiles.columns),
            columns,
        )

        self.assertEqual(extracted.operating_profiles.index.names, ["file_id"])

    def test_transform(self):
        # setup
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        self.assertEqual(transformed.operating_profiles.shape[0], 8)

        self.assertCountEqual(
            list(transformed.operating_profiles.columns),
            columns,
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
        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        self.assertEqual(extracted.operating_profiles.shape[0], 20)

        self.assertCountEqual(
            list(extracted.operating_profiles.columns),
            columns,
        )

        self.assertEqual(extracted.operating_profiles.index.names, ["file_id"])

    def test_transform(self):
        # setup
        file_id = hash(self.file_obj.file)
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        self.assertEqual(transformed.operating_profiles.shape[0], 20)

        self.assertCountEqual(
            list(transformed.operating_profiles.columns),
            columns,
        )

    def test_load(self):
        # setup
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        operating_profiles = OperatingProfile.objects.all()
        # test

        self.assertEqual(10, operating_profiles.count())


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingProfilesVehicleJourneysWithHolidays(ExtractBaseTestCase):

    test_file = (
        "data/test_operating_profiles/test_operating_profiles_vehicle_journeys.xml"
    )

    def test_transform(self):
        setup_bank_holidays()
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        self.assertEqual(extracted.operating_profiles.shape[0], 50)
        self.assertEqual(transformed.operating_profiles.shape[0], 50)

        self.assertCountEqual(
            list(extracted.operating_profiles.columns),
            columns,
        )

        self.assertCountEqual(
            list(transformed.operating_profiles.columns),
            columns,
        )

    def test_load(self):
        # setup
        setup_bank_holidays()
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)
        self.feed_parser.load(transformed)

        operating_profiles = OperatingProfile.objects.all()

        self.assertEqual(10, operating_profiles.count())


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingProfilesServicesWithHolidays(ExtractBaseTestCase):
    test_file = "data/test_operating_profiles/test_operating_profiles_services.xml"

    def test_transform(self):
        # setup
        setup_bank_holidays()
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)

        self.assertEqual(extracted.operating_profiles.shape[0], 32)
        self.assertEqual(transformed.operating_profiles.shape[0], 32)

        self.assertCountEqual(
            list(extracted.operating_profiles.columns),
            columns,
        )

        self.assertCountEqual(
            list(transformed.operating_profiles.columns),
            columns,
        )

    def test_load(self):
        # setup
        setup_bank_holidays()
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        # test
        transformed = self.feed_parser.transform(extracted)
        self.feed_parser.load(transformed)

        operating_profiles = OperatingProfile.objects.all()

        self.assertEqual(8, operating_profiles.count())
