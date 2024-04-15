import logging
import csv
from io import StringIO
import pandas as pd
import numpy as np
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
from typing import Tuple, Set

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


def create_df_timetable_visualiser(df_vehicle_journey: pd.DataFrame) -> pd.DataFrame:
    
    """
    Create the data frame for the timetable visualiser based on stops/atco codes
    and the vehicle journey codes
    """
    
    atco_codes = set()
    vehicle_journey_codes = set()
    data_df = []
    data = {}
    return pd.DataFrame()
    for _, row in df_vehicle_journey.iterrows():
        atco_code = row['atco_code']
        vehicle_journey_code = row['vehicle_journey_code']
        key = vehicle_journey_code+"_"+atco_code
        data[key] = row['departure_time']
        atco_codes.add(atco_code)
        vehicle_journey_codes.add(vehicle_journey_code)

    
    for atco_code in atco_codes:
        obj = {}
        for journey_code in vehicle_journey_codes_sorted:
            key = journey_code+"_"+atco_code
            val = data.get(key, "-")
            obj[journey_code] = val
        data_df.append(obj)
    #print(data_df)

    #bus_stops = list(bus_stop.values())
    df = pd.DataFrame(data_df)
    df = pd.DataFrame(data_df, index=stops)
    #print("df: ", df.head(n=100))
    df.to_csv("data_df.csv")


def get_df_timetable_visualiser(
    df_vehicle_journey_operating: pd.DataFrame,
) -> pd.DataFrame:
    """
    Get the dataframe containing the list of stops and the timetable details
    with journey code as columns
    """

    if df_vehicle_journey_operating.empty:
        return df_vehicle_journey_operating

    # Remove the extra columns from dataframe
    columns_to_keep = [
        "common_name",
        "stop_sequence",
        "vehicle_journey_code",
        "departure_time",
        "atco_code",
    ]
    df_vehicle_journey_operating = df_vehicle_journey_operating[columns_to_keep]
    df_vehicle_journey_operating = df_vehicle_journey_operating.drop_duplicates()

    # Get the unique sorted vehicle journey codes based on the departure time
    df_vehicle_journey_grouped = df_vehicle_journey_operating.groupby(
        by="vehicle_journey_code"
    )
    df_vehicle_journey_grouped = df_vehicle_journey_grouped.agg(
        {"departure_time": "min"}
    )
    df_vehicle_journey_sorted = df_vehicle_journey_grouped.sort_values(
        by="departure_time"
    )
    df_vehicle_journey_sorted = df_vehicle_journey_sorted.reset_index()
    vehicle_journey_codes_sorted = df_vehicle_journey_sorted["vehicle_journey_code"]

    # Add a new column stating the vehicle journey order based on vehicle journey codes order
    vehicle_journey_codes_sorted_dict = {
        code: index for index, code in enumerate(vehicle_journey_codes_sorted)
    }
    df_vehicle_journey_operating[
        "vehicle_journey_order"
    ] = df_vehicle_journey_operating["vehicle_journey_code"].replace(
        vehicle_journey_codes_sorted_dict
    )

    # Sort the data frame based on the vehicle journey and the stop sequence
    df_vehicle_journey_operating = df_vehicle_journey_operating.sort_values(
        by=["vehicle_journey_order", "stop_sequence"]
    )
    df_vehicle_journey_operating.to_csv("df_vehicle_journey_operating_sorted.csv")
    # TODO: Add the logic for creating the final dataframe of timetable

    df_vehicle_journey_operating['atco_sequence'] = df_vehicle_journey_operating.apply(lambda row: str(row['stop_sequence']) + "_" +row['atco_code'] , axis=1)    
    atco_codes_sequence = list(df_vehicle_journey_operating['atco_sequence'].unique())
    vehicle_journey_codes_sorted = list(df_vehicle_journey_operating['vehicle_journey_code'].unique())

    df_vehicle_journey_operating.to_csv("df_vehicle_journey_operating_11.csv")
    data = {}
    stops = {}
    for row in df_vehicle_journey_operating.to_dict('records'):
        sequence = row['stop_sequence']
        key = str(sequence) + "_" +row['vehicle_journey_code']
        data[key] = row['departure_time']
        if sequence not in stops:
            stops[sequence] = row["common_name"]

    print(f"Stops Unsorted: ", stops)
    bus_stop_sequences = list(stops.keys())
    bus_stop_sequences.sort()
    stops = {k: stops[k] for k in bus_stop_sequences}

    print(f"Stops Sorted: ", stops)
    
    data_df = []
    # vehicle_journey_codes = ['6001']
    
    print(f"Sequences: ", bus_stop_sequences)
    for seqeunce in bus_stop_sequences:
        obj = {}
        # atco_code_list = atco_code_dtl.split("_")
        # seqeunce = atco_code_list[0]
        # atco_code = atco_code_list[1]
        #stops.append(atco_code)
        for journey_code in vehicle_journey_codes_sorted:
            key = str(seqeunce) + "_" + journey_code
            val = data.get(key, "-")
            obj[journey_code] = val
        #print(obj)
        #print("*"*20)
        data_df.append(obj)
    #print(data_df)

    #bus_stops = list(bus_stop.values())
    df = pd.DataFrame(data_df)
    print(stops.keys())
    df = pd.DataFrame(data_df, index=list(stops.values()))
    #print("df: ", df.head(n=100))
    df.to_csv("data_df.csv")

    return df_vehicle_journey_operating


def filter_df_serviced_org_operating(
    target_date: str,
    df_serviced_org_working_days: pd.DataFrame
) -> List:
    """
    Get the vehicle journeys non-operating based on the serviced organisation
    working days

    :return: List
    Return the non-operating vehicle journey ids
    """    
    if df_serviced_org_working_days.empty:
        return []
    df_serviced_org_working_days = df_serviced_org_working_days.drop_duplicates()
    df_serviced_org_working_days.sort_values(by=['start_date'])
    vehicle_journey_nonoperating = []

    # Step 1: Remove the vehicle journeys which are outside the start date and end date as we don't have information
    df_group_vehicle_journey_date = df_serviced_org_working_days.groupby(
        by="vehicle_journey_id"
    )    
    df_service_grouped = df_group_vehicle_journey_date.agg(
        {"start_date": "min", "end_date": "max"}
    )
    df_service_nonoperating = df_service_grouped[(target_date < df_service_grouped.start_date) | (target_date > df_service_grouped.end_date)]
    if not df_service_nonoperating.empty:
        vehicle_journey_nonoperating = df_service_nonoperating['vehicle_journey_id'].unique().tolist()
        df_serviced_org_working_days = df_serviced_org_working_days[~df_serviced_org_working_days['vehicle_journey_id'].isin(vehicle_journey_nonoperating)]
    
    # Step 2: Find out the vehicle journeys which are not operating and lies within start and end date on the target date
    df_service_nonoperating = df_serviced_org_working_days[(target_date >= df_serviced_org_working_days.start_date)
        & (target_date <= df_serviced_org_working_days.end_date) & (~df_serviced_org_working_days["operating_on_working_days"])]
    if not df_service_nonoperating.empty:
        vehicle_journey_nonoperating = df_service_nonoperating['vehicle_journey_id'].unique().tolist()
        df_serviced_org_working_days = df_serviced_org_working_days[~df_serviced_org_working_days['vehicle_journey_id'].isin(vehicle_journey_nonoperating)]

    # Step 3: Find out the vehicle journeys which are operating and fall outside the operating range
    df_service_operating = df_serviced_org_working_days[df_serviced_org_working_days["operating_on_working_days"]]
    df_service_operating.reset_index(inplace=True)    
    
    for idx, row in df_service_operating.iterrows():
        # Iterate till second last row
        if idx + 1 == len(df_service_operating):
            continue
        next_row = df_service_operating.iloc[idx+1]
        next_vj = next_row['vehicle_journey_id']
        vj = row['vehicle_journey_id']
        if vj != next_vj: # If the vehicle journey is matching with current
            continue
        if vj in vehicle_journey_nonoperating:
            continue
        if target_date > row['end_date'] and target_date < next_row['start_date']:
            vehicle_journey_nonoperating.append(vj)

    return vehicle_journey_nonoperating


def get_vehicle_journeys_operating_nonoperating(
    df_vehicle_journey_operating: pd.DataFrame,
    df_vehicle_journey_nonoperating: pd.DataFrame,
) -> Tuple[List, List, Set]:
    """
    Return the unique vehicle journey which are operating/non-operating and
    combination of both

    In returning tuple, first element contains the list of unique vehicle journey operating,
    second element contains the list of unique vehicle journey non-operating and
    third element contains the list of unique vehicle journeys operating and non-operating
    """

    # Get all the vehicle journey which are operating on date
    op_exception_vehicle_journey = []
    if (
        not df_vehicle_journey_operating.empty
        and "vehicle_journey_id" in df_vehicle_journey_operating.columns
    ):
        op_exception_vehicle_journey = (
            df_vehicle_journey_operating["vehicle_journey_id"].unique().tolist()
        )

    # Get all the vehicle journey which are not operating on date
    nonop_exception_vehicle_journey = []
    if (
        not df_vehicle_journey_nonoperating.empty
        and "vehicle_journey_id" in df_vehicle_journey_nonoperating.columns
    ):
        nonop_exception_vehicle_journey = (
            df_vehicle_journey_nonoperating["vehicle_journey_id"].unique().tolist()
        )

    # Get all vehicle journey which are operating/non-operating on date
    all_exception_vehicle_journey = set(
        op_exception_vehicle_journey + nonop_exception_vehicle_journey
    )

    return (
        op_exception_vehicle_journey,
        nonop_exception_vehicle_journey,
        all_exception_vehicle_journey,
    )


def get_df_operating_vehicle_journey(
    day_of_week: str,
    df_all_vehicle_journey: pd.DataFrame,
    op_exception_vehicle_journey: np.ndarray,
    nonop_exception_vehicle_journey: np.ndarray,
) -> pd.DataFrame:
    """Get the valid vehicle journey based on the exceptions in
    operating and non-operating tables.

    :return: DataFrame
            Returns dataframe containing the valid vehicle journey id
    """

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
