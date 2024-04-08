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
from typing import List, Optional, Tuple
import numpy as np
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



def get_index_stop(stops, elem):

    """
    Get the position of the element based on the next and the previous
    element of the stop
    """

    # If the element previous is None, then check out for the next element
    if elem['prev'] is None:        
        return get_index_stop(elem['next'])
    else: # If the previous element is there, found the position
        try:
            return stops.index(elem['prev'])
        except ValueError as ve:            
            return get_index_stop(stops, elem['next'])


def merge_bus_new_stops(bus_stops, new_stops):

    """
    Merge the bus stops and the new stops for the all journeys.
    """

    # Iterate over the new stops and place them in the bus_stops 
    for idx, el in enumerate(new_stops):        
        print("-"*30)
        print(f"Iterating stop: {el['stop']}")
        index_stop = get_index_stop(bus_stops, el)
        bus_stops.insert(index_stop+1, el['stop'])

def get_(df_vj_wo_fir_jou: pd.DataFrame):

    """
    Get the 
    """
    print(f"df_vehicle_journey_operating: {df_vj_wo_fir_jou}")
    df_vj_wo_fir_jou.reset_index(inplace=True, drop=True)
    df_vj_wo_fir_jou.to_csv("df_vj_wo_fir_jou.csv")
    data = {}
    atco_codes = []
    new_stops = []
    df_size = len(df_vj_wo_fir_jou)
    prev_row = None
    bus_stop = {}
    first_vj_code = None
    # Iterating over the data frame to retreive the stops
    for loop_idx, row in df_vj_wo_fir_jou.iterrows():
        print(f"loop_idx: {loop_idx}")
        
        atco_code = row["atco_code"]
        vj = row['vehicle_journey_code']
        name = row['common_name']        
        stop_name = row['common_name']
        
        key = vj+"_"+atco_code
        data[key] = row['departure_time']
        if atco_code not in bus_stop:
            bus_stop[atco_code] = stop_name

        if not first_vj_code:
            first_vj_code = vj
        
        # If first vehicle journey, add the stops
        if first_vj_code == vj:
            atco_codes.append(atco_code)
            prev_row = row
            continue
        
        if loop_idx +1 == df_size:
            next_row = next_atco_code = next_vj = None
        else:
            print(f"Checking row: {loop_idx+1}")
            next_row = df_vj_wo_fir_jou.iloc[loop_idx+1]
            next_atco_code = next_row['atco_code']
            next_vj = next_row['vehicle_journey_code']
        
        prev_vj = prev_row['vehicle_journey_code']
        prev_atco_code = prev_row['atco_code']
        print(f"next_stop: {next_atco_code}-{next_row}")
        print(f"- {next_vj}--{vj}")
        print(f", prev_stop: {prev_atco_code} - {prev_vj}")

        next_stop = None
        if next_vj and next_vj != vj:
            next_stop = next_atco_code
        
        prev_stop = None
        if prev_vj == vj:
            prev_stop = prev_atco_code

        obj = {"atco_code": atco_code, "prev": prev_stop, "next": next_stop, "name": stop_name}
        print("obj", obj)

        # If the atco code/node is not present, then need add the stop (based on prev and next) 
        if obj not in new_stops:
            print("Adding stop as new stop")
            new_stops.append(obj)
        
        # Update the current row as previous row
        prev_row = row

    print(f"new_stops: {new_stops}")
    #merge_bus_new_stops(atco_codes, new_stops)


def get_df_(df_vehicle_journey_operating: pd.DataFrame) -> pd.DataFrame:
    
    """
    Get the dataframe containing the list of stops and the timetable details 
    with journey code as columns
    """    

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)    

    # Remove the extra columns from dataframe
    columns_to_keep = ['common_name', 'stop_sequence', 'vehicle_journey_code', 'departure_time', 'atco_code']
    df_vehicle_journey_operating = df_vehicle_journey_operating[columns_to_keep]
    df_vehicle_journey_operating = df_vehicle_journey_operating.drop_duplicates()    
    #df_vehicle_journey_operating = df_vehicle_journey_operating.sort_values(by=['vehicle_journey_code', 'stop_sequence'])
    df_vehicle_journey_operating.to_csv('df_vehicle_journey_operating_sorted.csv')
    
    # Get the unique sorted vehicle journey codes based on the departure time
    df_vehicle_journey_grouped = df_vehicle_journey_operating.groupby(by='vehicle_journey_code')
    df_vehicle_journey_grouped = df_vehicle_journey_grouped.agg({'departure_time': "min"})    
    df_vehicle_journey_sorted = df_vehicle_journey_grouped.sort_values(by='departure_time')
    df_vehicle_journey_sorted = df_vehicle_journey_sorted.reset_index()
    vehicle_journey_codes_sorted = df_vehicle_journey_sorted["vehicle_journey_code"]

    # Replace the vehicle journey codes with order by adding a new column
    vehicle_journey_codes_sorted_dict = {code: index for index, code in enumerate(vehicle_journey_codes_sorted)}
    df_vehicle_journey_operating['vehicle_journey_sorted'] = df_vehicle_journey_operating['vehicle_journey_code'].\
                                                                replace(vehicle_journey_codes_sorted_dict)
    
    # Sort the data frame based on the vehicle journey and the stop sequence
    df_vehicle_journey_operating = df_vehicle_journey_operating.sort_values(by=['vehicle_journey_sorted', 'stop_sequence'])
    df_vehicle_journey_operating.to_csv('df_vehicle_journey_operating_sorted.csv')
    
    # line = {}
    # atco_codes = []
    # for index, row in df_first_bus_route.iterrows():
    #     atco_codes.append(row['atco_code'])
        #line[row['atco_code']] = row['stop_sequence']
        
    data = {}
    atco_codes = []
    # df_vj_wo_fir_jou = df_vehicle_journey_operating[df_vehicle_journey_operating['vehicle_journey_code'] != first_vehicle_journey]
    df_vj_wo_fir_jou = df_vehicle_journey_operating
    get_(df_vehicle_journey_operating)
    
    # stops = []
    # for el in atco_codes:
    #     print(f"Stop: {el}: {bus_stop[el]}")
    #     stops.append(bus_stop[el])

    # data_df = []
    # # vehicle_journey_codes = ['6001']
    # for atco_code in atco_codes:        
    #     obj = {}
    #     for journey_code in vehicle_journey_codes_sorted:
    #         key = journey_code+"_"+atco_code
    #         val = data.get(key, "-")
    #         obj[journey_code] = val
    #     data_df.append(obj)
    # #print(data_df)
    
    # #bus_stops = list(bus_stop.values())
    # df = pd.DataFrame(data_df)
    # df = pd.DataFrame(data_df, index=stops)
    # #print("df: ", df.head(n=100))
    # df.to_csv("data_df.csv")
    return pd.DataFrame()
    

def filter_df_serviced_org_operating(
    target_date: str,
    df_serviced_org_working_days: pd.DataFrame,
    all_exception_vehicle_journey: np.ndarray,
) -> Tuple[List, List]:
    """
    Get the vehicle journeys based on the serviced organisation
    working days and the operating/non-operating execptions

    :return: DataFrame
    Return the filtered dataframe based on the serviced organisation
    """

    df_serviced_org_working_days.to_csv("serviced.csv")

    # Remove the vehicle journey which are not running on target date (nonoperating exception)
    df_serviced_org_working_days = df_serviced_org_working_days[
        ~df_serviced_org_working_days["vehicle_journey_id"].isin(all_exception_vehicle_journey)
    ]

    # Get the operating and non-operating working days
    df_service_operating = df_serviced_org_working_days[df_serviced_org_working_days["operating_on_working_days"]]
    df_service_nonoperating = df_serviced_org_working_days[~df_serviced_org_working_days["operating_on_working_days"]]

    # Find the service which are operating within range of start and end date
    df_service_operating = df_service_operating[
        (target_date > df_serviced_org_working_days.start_date) & (target_date < df_serviced_org_working_days.end_date)
    ]

    # Exclude the service which are outside the earliest start and latest end date as non-operating
    df_group_vehicle_journey_date = df_service_nonoperating.groupby(
        by="vehicle_journey_id"
    )
        
    df_service_grouped = df_group_vehicle_journey_date.agg(
        {'start_date': "min", 'end_date': "max"}
    )
    df_service_nonoperating = df_service_grouped[
        (target_date < df_service_grouped.start_date)
        | (target_date > df_service_grouped.end_date)
    ]    

    # Split the vehicle journey based on the operating_on_working_days
    (
        vehicle_journey_operating,
        vehicle_journey_nonoperating,
        _,
    ) = get_vehicle_journeys_operating_nonoperating(df_service_operating, df_service_nonoperating)

    return (vehicle_journey_operating, vehicle_journey_nonoperating)


def get_vehicle_journeys_operating_nonoperating(
    df_vehicle_journey_operating: pd.DataFrame,
    df_vehicle_journey_nonoperating: pd.DataFrame,
) -> Tuple[List, List, List]:
    """
    Return the unique vehicle journey which are operating/non-operating and
    combination of both

    In returning tuple, first element contains the list of unique vehicle journey operating,
    second element contains the list of unique vehicle journey non-operating and
    third element contains the list of unique vehicle journeys operating and non-operating 
    """

    # Get all the vehicle journey which are operating on date
    op_exception_vehicle_journey = []
    if not df_vehicle_journey_operating.empty and 'vehicle_journey_id' in df_vehicle_journey_operating.columns:
        op_exception_vehicle_journey = df_vehicle_journey_operating[
            "vehicle_journey_id"
        ].unique().tolist()

    # Get all the vehicle journey which are not operating on date
    nonop_exception_vehicle_journey = []
    if not df_vehicle_journey_nonoperating.empty and 'vehicle_journey_id' in df_vehicle_journey_nonoperating.columns:
        nonop_exception_vehicle_journey = df_vehicle_journey_nonoperating[
            "vehicle_journey_id"
        ].unique().tolist()

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
    df_op_exception_vehicle_journey: pd.DataFrame,
    df_nonop_excecption_vehicle_journey: pd.DataFrame,
    op_exception_vehicle_journey: np.ndarray,
    nonop_exception_vehicle_journey: np.ndarray,
) -> pd.DataFrame:
    """Get the valid vehicle journey based on the exceptions in
    operating and non-operating tables.

    :return: DataFrame
            Returns dataframe containing the valid vehicle journey id
    """

    df_all_vehicle_journey.to_csv("base.csv")
    df_op_exception_vehicle_journey.to_csv("op_exception.csv")
    df_nonop_excecption_vehicle_journey.to_csv("nonop_exception.csv")

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

    get_df_operating_vehicle_journey(
        target_date,
        day_of_week,
        df_qs_all_vehicle_journeys,
        df_qs_vehicle_journey_op_exceptions,
        df_qs_vehicle_journey_nonop_exceptions,
    )
    return df_qs_all_vehicle_journeys
