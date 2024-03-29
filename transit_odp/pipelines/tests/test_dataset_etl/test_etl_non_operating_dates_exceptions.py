import pandas as pd
import datetime

from transit_odp.pipelines.tests.test_dataset_etl.test_extract_metadata import (
    ExtractBaseTestCase,
)
from waffle.testutils import override_flag

from transit_odp.transmodel.factories import BankHolidaysFactory
from transit_odp.transmodel.models import NonOperatingDatesExceptions, VehicleJourney

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
    BankHolidaysFactory(txc_element="MayDay", date=datetime.date(2024, 5, 6))
    BankHolidaysFactory(txc_element="ChristmasDay", date=datetime.date(2024, 12, 25))
    BankHolidaysFactory(txc_element="BoxingDay", date=datetime.date(2024, 12, 26))
    BankHolidaysFactory(
        txc_element="BoxingDayHoliday", date=datetime.date(2024, 12, 27)
    )
    BankHolidaysFactory(txc_element="GoodFriday", date=datetime.date(2024, 4, 7))
    BankHolidaysFactory(txc_element="NewYearsEve", date=datetime.date(2024, 12, 31))


@override_flag("is_timetable_visualiser_active", active=True)
class ETLNonOperatingDatesException(ExtractBaseTestCase):
    test_file = (
        "data/test_non_operating_dates_exception/test_non_op_dates_exceptions_mixed.xml"
    )

    def test_extract(self):
        setup_bank_holidays()
        # test
        extracted = self.trans_xchange_extractor.extract()

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
            pd.to_datetime("2023-09-29") in df_extracted_data["exceptions_date"].values
        )
        self.assertTrue(
            pd.to_datetime("2024-07-01") in df_extracted_data["exceptions_date"].values
        )
        # test bank holiday date
        self.assertTrue(
            pd.to_datetime("2024-12-26") in df_extracted_data["exceptions_date"].values
        )
        self.assertCountEqual(
            list(df_extracted_data.columns),
            columns,
        )
        self.assertEqual(481, df_extracted_data.shape[0])

    def test_load(self):
        # setup
        setup_bank_holidays()

        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        non_operating_dates_exception = NonOperatingDatesExceptions.objects.values_list(
            "non_operating_date", flat=True
        )
        # test
        self.assertEqual(46, non_operating_dates_exception.count())
        # Verify ChristmasDay in days of non-operation as it falls on the day in operating profile
        self.assertIn(datetime.date(2024, 12, 25), non_operating_dates_exception)
        # Verify MayDay holiday in non-operation exception as it falls on the day in operating profile
        self.assertIn(datetime.date(2024, 5, 6), non_operating_dates_exception)
        # Verify if the holiday not in non-operation exception as it falls outside the day in operating profile
        self.assertNotIn(datetime.date(2024, 12, 31), non_operating_dates_exception)


@override_flag("is_timetable_visualiser_active", active=True)
class ETLNonOperatingDatesExceptionServicesOnly(ExtractBaseTestCase):
    test_file = "data/test_non_operating_dates_exception/test_non_op_dates_exceptions_only_services.xml"

    def test_extract(self):
        setup_bank_holidays()
        # test
        extracted = self.trans_xchange_extractor.extract()

        df_extracted_data = extracted.operating_profiles

        df_extracted_data["exceptions_date"] = pd.to_datetime(
            df_extracted_data["exceptions_date"]
        )
        # This falls on a day in the operating profile
        self.assertTrue(
            pd.to_datetime("2022-09-19") in df_extracted_data["exceptions_date"].values
        )
        # ChristmasDay falls on the day in the operating profile
        self.assertTrue(
            pd.to_datetime("2024-12-25") in df_extracted_data["exceptions_date"].values
        )
        # BoxingDay falls on the day in the operating profile
        self.assertTrue(
            pd.to_datetime("2024-12-26") in df_extracted_data["exceptions_date"].values
        )
        # Operating period start should be conisdered
        self.assertTrue(
            pd.to_datetime("2024-05-06") in df_extracted_data["exceptions_date"].values
        )
        self.assertCountEqual(
            list(df_extracted_data.columns),
            columns,
        )
        self.assertEqual(135, df_extracted_data.shape[0])

    def test_load(self):
        # setup
        setup_bank_holidays()

        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        non_operating_dates_exception = NonOperatingDatesExceptions.objects.values_list(
            "non_operating_date", flat=True
        )
        # test
        self.assertEqual(15, non_operating_dates_exception.count())
        # Verify ChristmayDay date in days of non operation dates exception
        self.assertIn(datetime.date(2024, 12, 25), non_operating_dates_exception)
        # Verify New year eve    date in days of non operation dates exception
        self.assertIn(datetime.date(2024, 12, 31), non_operating_dates_exception)
        # Verify OtherPublicHoliday QueensJubilee date in days of non operation dates exception
        self.assertNotIn(datetime.date(2022, 6, 3), non_operating_dates_exception)


@override_flag("is_timetable_visualiser_active", active=True)
class ETLNonOperatingDatesExceptionsInOpProfile(ExtractBaseTestCase):
    test_file = "data/test_non_operating_dates_exception/test_non_op_dates_exceptions_outside_op_profiles.xml"

    def test_extract(self):
        setup_bank_holidays()
        # test
        extracted = self.trans_xchange_extractor.extract()

        df_extracted_data = extracted.operating_profiles

        df_extracted_data["exceptions_date"] = pd.to_datetime(
            df_extracted_data["exceptions_date"]
        )

        self.assertTrue(
            pd.to_datetime("2022-09-19") in df_extracted_data["exceptions_date"].values
        )
        self.assertCountEqual(
            list(df_extracted_data.columns),
            columns,
        )
        self.assertEqual(81, df_extracted_data.shape[0])

    def test_load(self):
        setup_bank_holidays()

        extracted = self.trans_xchange_extractor.extract()
        transformed = self.feed_parser.transform(extracted)

        self.feed_parser.load(transformed)

        non_operating_dates_exception = NonOperatingDatesExceptions.objects.values_list(
            "non_operating_date", flat=True
        )
        # test
        self.assertEqual(9, non_operating_dates_exception.count())
        # Verify GoodFriday is not in the non operating exceptions
        # as it already falls outside the op profile
        self.assertNotIn(datetime.date(2024, 3, 29), non_operating_dates_exception)
        # Verify EasterMonday is not in the non operating exceptions
        # as it already falls outside the op profile
        self.assertNotIn(datetime.date(2024, 4, 1), non_operating_dates_exception)
        # Verify SpringBank is not in the non operating exceptions
        # as it already falls outside the op profile
        self.assertNotIn(datetime.date(2023, 5, 27), non_operating_dates_exception)
        # Verify OtherBankHoliday QueensJubilee is not in the non operating exceptions
        # as it already falls outside the op profile
        self.assertNotIn(datetime.date(2022, 3, 6), non_operating_dates_exception)
        # Verify CoronationOfKingCharlesIII is not in the non operating exceptions
        # as it already falls outside the op profile
        self.assertNotIn(datetime.date(2023, 5, 8), non_operating_dates_exception)
