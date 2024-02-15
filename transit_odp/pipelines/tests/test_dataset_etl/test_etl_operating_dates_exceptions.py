import pandas as pd
import datetime

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from waffle.testutils import override_flag

from transit_odp.transmodel.factories import BankHolidaysFactory
from transit_odp.transmodel.models import OperatingDatesExceptions

columns = [
    "service_code",
    "vehicle_journey_code",
    "serviced_org_ref",
    "operational",
    "day_of_week",
    "exceptions_operational",
    "exceptions_date",
]


def setup_bank_holidays():
    BankHolidaysFactory(txc_element="ChristmasDay", date=datetime.date(2024, 12, 25))
    BankHolidaysFactory(txc_element="BoxingDay", date=datetime.date(2024, 12, 26))
    BankHolidaysFactory(
        txc_element="BoxingDayHoliday", date=datetime.date(2024, 12, 27)
    )
    BankHolidaysFactory(txc_element="GoodFriday", date=datetime.date(2024, 3, 29))


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingDatesException(ExtractBaseTestCase):
    test_file = "data/test_operating_dates_exception/test_op_dates_exceptions.xml"

    def test_extract(self):
        setup_bank_holidays()
        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        df_extracted_data = extracted.operating_profiles

        df_extracted_data["exceptions_date"] = pd.to_datetime(
            df_extracted_data["exceptions_date"]
        )
        date_range = pd.date_range(
            start=pd.to_datetime("2024-07-22"),
            end=pd.to_datetime("2024-08-30"),
            freq="D",
        )

        self.assertTrue(
            all(
                date in df_extracted_data["exceptions_date"].to_list()
                for date in date_range
            )
        )
        self.assertTrue(
            pd.to_datetime("2023-11-30") in df_extracted_data["exceptions_date"].values
        )
        self.assertCountEqual(
            list(df_extracted_data.columns),
            columns,
        )
        self.assertEqual(510, df_extracted_data.shape[0])

    def test_transform(self):
        setup_bank_holidays()
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        # test
        transformed = self.feed_parser.transform(extracted)

        df_extracted_data = transformed.operating_profiles

        df_extracted_data["exceptions_date"] = pd.to_datetime(
            df_extracted_data["exceptions_date"]
        )
        date_range = pd.date_range(
            start=pd.to_datetime("2024-07-22"),
            end=pd.to_datetime("2024-08-30"),
            freq="D",
        )
        self.assertTrue(
            all(
                date in df_extracted_data["exceptions_date"].to_list()
                for date in date_range
            )
        )
        self.assertTrue(
            pd.to_datetime("2023-11-30") in df_extracted_data["exceptions_date"].values
        )
        self.assertCountEqual(
            list(df_extracted_data.columns),
            columns,
        )
        self.assertEqual(510, df_extracted_data.shape[0])

    def test_load(self):
        # setup
        setup_bank_holidays()

        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        operating_dates_exception = OperatingDatesExceptions.objects.values_list(
            "operating_date", flat=True
        )
        # test
        self.assertEqual(16, operating_dates_exception.count())
        # Verify bank holiday date in days of operation tag
        self.assertIn(datetime.date(2024, 12, 25), operating_dates_exception)
        # Verify other bank holiday date in days of operation tag
        self.assertIn(datetime.date(2024, 2, 13), operating_dates_exception)
        # Verify day of operation for operating profile with HolidaysOnly
        self.assertIn(datetime.date(2023, 9, 15), operating_dates_exception)
        # Verify other bank holiday date is not in the table as
        # it falls on the day of the week mentioned in operating profile
        self.assertNotIn(datetime.date(2024, 2, 16), operating_dates_exception)
        # Verify days of operation date is not in the table as
        # it falls on the day of the week mentioned in operating profile
        self.assertNotIn(datetime.date(2023, 11, 30), operating_dates_exception)
        # Verify bank holiday date is not in the table as
        # it falls on the day of the week mentioned in operating profile
        self.assertNotIn(datetime.date(2024, 3, 29), operating_dates_exception)


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingDatesExceptionServicesOnly(ExtractBaseTestCase):
    test_file = (
        "data/test_operating_dates_exception/test_op_dates_exception_services_only.xml"
    )

    def test_extract(self):
        setup_bank_holidays()
        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        df_extracted_data = extracted.operating_profiles

        df_extracted_data["exceptions_date"] = pd.to_datetime(
            df_extracted_data["exceptions_date"]
        )
        date_range = pd.date_range(
            start=pd.to_datetime("2023-11-30"),
            end=pd.to_datetime("2023-12-31"),
            freq="D",
        )
        second_date_range = pd.date_range(
            start=pd.to_datetime("2024-07-22"),
            end=pd.to_datetime("2024-08-30"),
            freq="D",
        )
        list_exception_dates = df_extracted_data["exceptions_date"].to_list()
        self.assertTrue(all(date in list_exception_dates for date in date_range))
        self.assertTrue(all(date in list_exception_dates for date in second_date_range))
        self.assertTrue(
            pd.to_datetime("2023-09-29") in df_extracted_data["exceptions_date"].values
        )
        self.assertCountEqual(
            list(df_extracted_data.columns),
            columns,
        )
        self.assertEqual(1280, df_extracted_data.shape[0])

    def test_transform(self):
        # setup
        file_id = hash(self.file_obj.file)
        setup_bank_holidays()
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        # test
        transformed = self.feed_parser.transform(extracted)

        df_extracted_data = transformed.operating_profiles

        df_extracted_data["exceptions_date"] = pd.to_datetime(
            df_extracted_data["exceptions_date"]
        )
        date_range = pd.date_range(
            start=pd.to_datetime("2023-11-30"),
            end=pd.to_datetime("2023-12-31"),
            freq="D",
        )
        second_date_range = pd.date_range(
            start=pd.to_datetime("2024-07-22"),
            end=pd.to_datetime("2024-08-30"),
            freq="D",
        )
        list_exception_dates = df_extracted_data["exceptions_date"].to_list()
        self.assertTrue(all(date in list_exception_dates for date in date_range))
        self.assertTrue(all(date in list_exception_dates for date in second_date_range))
        self.assertTrue(
            pd.to_datetime("2023-09-29") in df_extracted_data["exceptions_date"].values
        )
        self.assertCountEqual(
            list(df_extracted_data.columns),
            columns,
        )
        self.assertEqual(1280, df_extracted_data.shape[0])

    def test_load(self):
        # setup
        setup_bank_holidays()

        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        operating_dates_exception = OperatingDatesExceptions.objects.values_list(
            "operating_date", flat=True
        )
        # test
        self.assertEqual(60, operating_dates_exception.count())
        # Verify bank holiday date in days of operation tag
        self.assertIn(datetime.date(2023, 12, 25), operating_dates_exception)
        # Verify other bank holiday date in days of operation tag
        self.assertIn(datetime.date(2024, 2, 12), operating_dates_exception)
        # Verify other bank holiday date is not in the table as
        # it falls on the day of the week mentioned in operating profile
        self.assertNotIn(datetime.date(2024, 2, 16), operating_dates_exception)
        # Verify days of operation date is not in the table as
        # it falls on the day of the week mentioned in operating profile
        self.assertNotIn(datetime.date(2023, 12, 1), operating_dates_exception)


@override_flag("is_timetable_visualiser_active", active=True)
class ETLOperatingDatesExceptionVehicleJourneysOnly(ExtractBaseTestCase):
    test_file = "data/test_operating_dates_exception/test_op_dates_exceptions.xml"

    def test_extract(self):
        setup_bank_holidays()
        # test
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)

        df_extracted_data = extracted.operating_profiles

        df_extracted_data["exceptions_date"] = pd.to_datetime(
            df_extracted_data["exceptions_date"]
        )
        date_range = pd.date_range(
            start=pd.to_datetime("2024-07-22"),
            end=pd.to_datetime("2024-08-30"),
            freq="D",
        )

        self.assertTrue(
            all(
                date in df_extracted_data["exceptions_date"].to_list()
                for date in date_range
            )
        )
        self.assertTrue(
            pd.to_datetime("2023-11-30") in df_extracted_data["exceptions_date"].values
        )
        self.assertCountEqual(
            list(df_extracted_data.columns),
            columns,
        )
        self.assertEqual(510, df_extracted_data.shape[0])

    def test_transform(self):
        setup_bank_holidays()
        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        # test
        transformed = self.feed_parser.transform(extracted)

        df_extracted_data = transformed.operating_profiles

        df_extracted_data["exceptions_date"] = pd.to_datetime(
            df_extracted_data["exceptions_date"]
        )
        date_range = pd.date_range(
            start=pd.to_datetime("2024-07-22"),
            end=pd.to_datetime("2024-08-30"),
            freq="D",
        )
        self.assertTrue(
            all(
                date in df_extracted_data["exceptions_date"].to_list()
                for date in date_range
            )
        )
        self.assertTrue(
            pd.to_datetime("2023-11-30") in df_extracted_data["exceptions_date"].values
        )
        self.assertCountEqual(
            list(df_extracted_data.columns),
            columns,
        )
        self.assertEqual(510, df_extracted_data.shape[0])

    def test_load(self):
        # setup
        setup_bank_holidays()

        extracted = self.xml_file_parser._extract(self.doc, self.file_obj)
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        operating_dates_exception = OperatingDatesExceptions.objects.values_list(
            "operating_date", flat=True
        )
        # test
        self.assertEqual(16, operating_dates_exception.count())
        # Verify bank holiday date in days of operation tag
        self.assertIn(datetime.date(2024, 12, 25), operating_dates_exception)
        # Verify other bank holiday date in days of operation tag
        self.assertIn(datetime.date(2024, 2, 13), operating_dates_exception)
        # Verify day of operation for operating profile with HolidaysOnly
        self.assertIn(datetime.date(2023, 9, 15), operating_dates_exception)
        # Verify other bank holiday date is not in the table as
        # it falls on the day of the week mentioned in operating profile
        self.assertNotIn(datetime.date(2024, 2, 16), operating_dates_exception)
        # Verify days of operation date is not in the table as
        # it falls on the day of the week mentioned in operating profile
        self.assertNotIn(datetime.date(2023, 11, 30), operating_dates_exception)
        # Verify bank holiday date is not in the table as
        # it falls on the day of the week mentioned in operating profile
        self.assertNotIn(datetime.date(2024, 3, 29), operating_dates_exception)
