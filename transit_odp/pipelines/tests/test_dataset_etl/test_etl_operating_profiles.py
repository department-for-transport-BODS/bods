from dateutil import tz
from transit_odp.pipelines.tests.test_dataset_etl.test_etl_operating_dates_exceptions import (
    setup_bank_holidays,
)

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)

from transit_odp.transmodel.models import OperatingProfile, ServicePatternStop
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
        extracted = self.trans_xchange_extractor.extract()

        self.assertEqual(extracted.operating_profiles.shape[0], 8)

        self.assertCountEqual(
            list(extracted.operating_profiles.columns),
            columns,
        )

        self.assertEqual(extracted.operating_profiles.index.names, ["file_id"])

    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)

        self.assertEqual(transformed.operating_profiles.shape[0], 8)

        self.assertCountEqual(
            list(transformed.operating_profiles.columns),
            columns,
        )

    def test_load(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
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
        extracted = self.trans_xchange_extractor.extract()

        self.assertEqual(extracted.operating_profiles.shape[0], 474)

        self.assertCountEqual(
            list(extracted.operating_profiles.columns),
            columns,
        )

        self.assertEqual(extracted.operating_profiles.index.names, ["file_id"])

    def test_transform(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)

        self.assertEqual(transformed.operating_profiles.shape[0], 259)

        self.assertCountEqual(
            list(transformed.operating_profiles.columns),
            columns,
        )

    def test_load(self):
        # setup
        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        operating_profiles = OperatingProfile.objects.all()
        # test

        self.assertEqual(237, operating_profiles.count())


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingProfilesVehicleJourneysWithHolidays(ExtractBaseTestCase):
    test_file = (
        "data/test_operating_profiles/test_operating_profiles_vehicle_journeys.xml"
    )

    def test_transform(self):
        setup_bank_holidays()
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)

        self.assertEqual(extracted.operating_profiles.shape[0], 1163)
        self.assertEqual(transformed.operating_profiles.shape[0], 948)

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
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)
        self.feed_parser.load(transformed)

        operating_profiles = OperatingProfile.objects.all()

        self.assertEqual(237, operating_profiles.count())


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingProfilesServicesWithHolidays(ExtractBaseTestCase):
    test_file = "data/test_operating_profiles/test_operating_profiles_services.xml"

    def test_transform(self):
        # setup
        setup_bank_holidays()
        extracted = self.trans_xchange_extractor.extract()

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
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)
        self.feed_parser.load(transformed)

        operating_profiles = OperatingProfile.objects.all()

        self.assertEqual(8, operating_profiles.count())


# Test operating profiles when there are no exceptions during the operating period dates
@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingProfilesWithSmalleroperatingPeriods(ExtractBaseTestCase):
    test_file = "data/test_operating_profiles/test_operating_profiles_with_smaller_operating_periods.xml"

    def test_load(self):
        # setup
        setup_bank_holidays()
        extracted = self.trans_xchange_extractor.extract()

        # test
        transformed = self.feed_parser.transform(extracted)
        self.feed_parser.load(transformed)

        operating_profiles = OperatingProfile.objects.all()
        service_pattern_stops = ServicePatternStop.objects.all()

        self.assertEqual(521, operating_profiles.count())
        self.assertEqual(2478, service_pattern_stops.count())


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingProfilesServices(ExtractBaseTestCase):
    """
    Test case for extracting operating profiles from a TransXChange file.
    Ensure that the extracted operating profiles DataFrame
    meets the expected structure and values.
    Specifically check that if both the WorkingDays and Holidays are missing from the ServicedOrgRef element,
    then the serviced_org_ref property in the df should be None.

    """

    test_file = "data/test_operating_profiles/test_operating_profiles_missing_working_days_holidays_serviced_org_ref.xml"

    def test_extract(self):
        # test
        extracted = self.trans_xchange_extractor.extract()
        self.assertEqual(extracted.operating_profiles.shape[0], 70)

        self.assertEqual(extracted.operating_profiles.index.names, ["file_id"])

        self.assertIn("serviced_org_ref", extracted.operating_profiles.columns)

        self.assertTrue(
            extracted.operating_profiles["serviced_org_ref"].isnull().all(),
            "Not all 'serviced_org_ref' values are None",
        )
