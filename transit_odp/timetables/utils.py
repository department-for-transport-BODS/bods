import logging
import csv
from io import StringIO
import pandas as pd

from transit_odp.pipelines.constants import SchemaCategory
from transit_odp.pipelines.models import SchemaDefinition
from transit_odp.pipelines.pipelines.xml_schema import SchemaLoader
from transit_odp.timetables.constants import TXC_XSD_PATH
from django.conf import settings

import requests
from requests import RequestException

from enum import Enum
from pydantic import BaseModel, ValidationError, Field
from typing import List, Optional
from datetime import datetime, timedelta

from transit_odp.common.utils.s3_bucket_connection import get_s3_bucket_storage

from transit_odp.transmodel.models import BankHolidays

logger = logging.getLogger(__name__)


def get_transxchange_schema():
    definition = SchemaDefinition.objects.get(category=SchemaCategory.TXC)
    schema_loader = SchemaLoader(definition, TXC_XSD_PATH)
    return schema_loader.schema


def read_delete_datasets_file_from_s3():
    try:
        storage = get_s3_bucket_storage()
        file_name = "delete_datasets.csv"

        if not storage.exists(file_name):
            logger.warning(f"{file_name} does not exist in the S3 bucket.")
            return []

        file = storage._open(file_name)
        content = file.read().decode()
        file.close()

        # Remove BOM character if present
        if content.startswith("\ufeff"):
            content = content.lstrip("\ufeff")

        csv_file = StringIO(content)
        reader = csv.DictReader(csv_file)
        dataset_ids = [
            int(row["Dataset ID"]) for row in reader if row["Dataset ID"].strip()
        ]

        if dataset_ids:
            logger.info(
                f"Successfully read {len(dataset_ids)} dataset IDs from {file_name} in S3."
            )
        else:
            logger.warning(
                f"{file_name} in S3 is empty or does not contain valid dataset IDs."
            )

        return dataset_ids
    except Exception as e:
        logger.error(f"Error reading {file_name} from S3: {str(e)}")
        raise


class HolidaysNonSubstituteEnum(Enum):
    NewYearsDay = "New Year's Day"
    ChristmasDay = "Christmas Day"
    BoxingDay = "Boxing Day"
    GoodFriday = "Good Friday"
    EasterMonday = "Easter Monday"
    MayDay = "Early May bank holiday"
    SpringBank = "Spring bank holiday"
    LateSummerBankHolidayNotScotland = "Summer bank holiday"
    Jan2ndScotland = "2nd January"
    StAndrewsDay = "St Andrew's Day"
    AugustBankHolidayScotland = "Summer bank holiday"


class HolidaysSubstituteEnum(Enum):
    NewYearsDayHoliday = "New Year's Day"
    ChristmasDayHoliday = "Christmas Day"
    BoxingDayHoliday = "Boxing Day"
    Jan2ndScotlandHoliday = "2nd January"
    StAndrewsDayHoliday = "St Andrew's Day"


class Event(BaseModel):
    title: str
    date: str
    notes: Optional[str] = ""
    bunting: bool


class Division(BaseModel):
    division: str
    events: List[Event]


class APIBankHolidays(BaseModel):
    england_and_wales: Division = Field(alias="england-and-wales")
    scotland: Division


def get_json_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        json_response = response.json()
        return json_response
    except RequestException as e:
        logger.error(f"Error obtaining json data from the endpoint {url}: {str(e)}")
        raise


def get_holiday_substitute(holiday, is_substitute):
    try:
        if is_substitute:
            day_enum = HolidaysSubstituteEnum(holiday.replace("’", "'"))
        else:
            day_enum = HolidaysNonSubstituteEnum(holiday.replace("’", "'"))

        return day_enum.name
    except ValueError as e:
        logger.error(
            f"Error obtaining bank holiday element for holiday - {holiday}: {str(e)}"
        )
        raise


def is_christmas_or_new_year(date):
    return (date.month == 12 and date.day == 25) or (date.month == 1 and date.day == 1)


def is_eve(date, month, day):
    return date.month == month and date.day == day


def get_holiday_obj(division, date, holiday):
    try:
        txc_element = ""

        if is_eve(date, 12, 31):
            txc_element = "NewYearsEve"
        elif is_eve(date, 12, 24):
            txc_element = "ChristmasEve"
        else:
            txc_element = get_holiday_substitute(
                holiday["title"], bool(holiday["notes"])
            )

        return {
            "txc_element": txc_element,
            "title": holiday["title"],
            "date": date,
            "notes": holiday["notes"],
            "division": division,
        }
    except Exception as e:
        logger.error(f"Exception while returning the holiday object - {str(e)}")
        return None


def get_bank_holiday_obj(division: str, holiday: dict):
    date = datetime.strptime(holiday["date"], "%Y-%m-%d").date()
    is_holiday_eve = is_christmas_or_new_year(date)
    obj_holiday = []

    db_holiday = get_holiday_obj(division, date, holiday)
    if db_holiday:
        obj_holiday.append(db_holiday)
    if is_holiday_eve:
        db_holiday = get_holiday_obj(division, date - timedelta(days=1), holiday)
        if db_holiday:
            obj_holiday.append(db_holiday)

    return obj_holiday


def get_bank_holidays():
    try:
        json_bank_holidays = get_json_data(settings.BANK_HOLIDAY_API_URL)

        df_bank_holidays = []
        parsed_response = APIBankHolidays.model_validate(json_bank_holidays)
        for division_name, division_data in parsed_response.model_dump().items():
            division_name = division_data["division"]
            for event in division_data["events"]:
                df_bank_holidays.extend(get_bank_holiday_obj(division_name, event))

        return df_bank_holidays
    except ValidationError as e:
        for error in e.errors():
            logger.error(f"Bank holiday validation error - {error}")
        raise
    except Exception as e:
        logger.error(f"Exception while obtaining bank holidays from the api: {str(e)}")
        raise


def get_holidays_records_to_insert(records):
    for record in records:
        if record is not None:
            yield BankHolidays(
                txc_element=record["txc_element"],
                title=record["title"],
                date=record["date"],
                notes=record["notes"],
                division=record["division"],
            )


def filter_rows_by_journeys(row, journey_mapping):
    date_obj = row["exceptions_date"]
    if date_obj:
        day_of_week = date_obj.strftime("%A")
        if row["exceptions_operational"] == True:
            return day_of_week not in journey_mapping[row["vehicle_journey_code"]]
        return day_of_week in journey_mapping[row["vehicle_journey_code"]]
    else:
        return False


def get_line_description_based_on_direction(row: pd.Series) -> str:
    direction_mapping = {
        "inbound": row["inbound_description"],
        "outbound": row["outbound_description"],
        "clockwise": row["outbound_description"],
        "antiClockwise": row["inbound_description"],
    }
    return direction_mapping.get(row["direction"], "")


def filter_df_serviced_org_operating(
    target_date: str,
    day_of_week: str,
    df_service: pd.DataFrame,
    df_op_exception_vehicle_journey: pd.DataFrame,
    df_nonop_excecption_vehicle_journey: pd.DataFrame,
) -> pd.DataFrame:
    """
    Get the vehicle journeys based on the serviced organisation
    working days and the operating/non-operating execptions

    :return: DataFrame
    Return the filtered dataframe
    """

    # base_df = base_df.drop(columns=[])
    df_service.to_csv("serviced.csv")
    nonop_exception_vehicle_journey = df_nonop_excecption_vehicle_journey[
        "vehicle_journey_id"
    ].unique()

    # Filtered based on serviced organisation id
    serviced_org_id = [14, 15]
    df_service = df_service[df_service["serviced_org_id"].isin(serviced_org_id)]

    # Remove the vehicle journey which are not running on target date (nonoperating exception)
    df_service = df_service[
        ~df_service["vehicle_journey_id"].isin(nonop_exception_vehicle_journey)
    ]

    # Split the vehicle journey based on the operating_on_working_days
    df_service_operating = df_service[df_service["operating_on_working_days"]]
    df_service_non_operating = df_service[~df_service["operating_on_working_days"]]
    df_service_operating = df_service_operating[
        (df_service_operating.start_date < target_date)
        & (target_date < df_service_operating.end_date)
    ]

    """ 
    
    """

    return None


def filter_df_on_exceptions(
    day_of_week: str,
    df_all_vehicle_journey: pd.DataFrame,
    df_op_exception_vehicle_journey: pd.DataFrame,
    df_nonop_excecption_vehicle_journey: pd.DataFrame,
) -> pd.DataFrame:
    """Get the valid vehicle journey based on the exceptions in
    operating and non-operating tables.

    :return: DataFrame
            Returns dataframe containing the valid vehicle journey id
    """

    # base_df = base_df.drop(columns=[])
    df_all_vehicle_journey.to_csv("base.csv")
    df_op_exception_vehicle_journey.to_csv("op_exception.csv")
    df_nonop_excecption_vehicle_journey.to_csv("nonop_exception.csv")

    op_exception_vehicle_journey = df_op_exception_vehicle_journey[
        "vehicle_journey_id"
    ].unique()
    nonop_exception_vehicle_journey = df_nonop_excecption_vehicle_journey[
        "vehicle_journey_id"
    ].unique()

    # Filter the dataframe based on the day of week or in the operating exception
    df_operating_vehicle_journey = df_all_vehicle_journey.loc[
        (df_all_vehicle_journey["day_of_week"] == day_of_week)
        | (
            df_all_vehicle_journey["vehicle_journey_id"].isin(
                op_exception_vehicle_journey
            )
        )
    ]

    # Remove the vehicle journey which are not running on target date (nonoperating exception)
    df_operating_vehicle_journey = df_operating_vehicle_journey[
        ~df_operating_vehicle_journey["vehicle_journey_id"].isin(
            nonop_exception_vehicle_journey
        )
    ]

    return df_operating_vehicle_journey


def convert_queryset_to_dataframe(queryset: list):
    return pd.DataFrame.from_records(queryset)


def get_dataframe_from_queryset(
    target_date,
    day_of_week,
    queryset_all_vehicle_journeys: list,
    queryset_serviced_orgs: list,
    queryset_vehicle_journey_op_exceptions: list,
    queryset_vehicle_journey_nonop_exceptions: list,
) -> pd.DataFrame:
    df_qs_all_vehicle_journeys = pd.DataFrame.from_records(
        queryset_all_vehicle_journeys
    )
    df_qs_serviced_org = pd.DataFrame.from_records(queryset_serviced_orgs)
    df_qs_vehicle_journey_op_exceptions = pd.DataFrame.from_records(
        queryset_vehicle_journey_op_exceptions
    )
    df_qs_vehicle_journey_nonop_exceptions = pd.DataFrame.from_records(
        queryset_vehicle_journey_nonop_exceptions
    )

    filter_df_on_exceptions(
        target_date,
        day_of_week,
        df_qs_all_vehicle_journeys,
        df_qs_vehicle_journey_op_exceptions,
        df_qs_vehicle_journey_nonop_exceptions,
    )
    return df_qs_all_vehicle_journeys
