import logging
import json
import pandas as pd
from transit_odp.pipelines.constants import SchemaCategory
from transit_odp.pipelines.models import SchemaDefinition
from transit_odp.pipelines.pipelines.xml_schema import SchemaLoader
from transit_odp.timetables.constants import TXC_XSD_PATH
from django.conf import settings
from transit_odp.dqs.constants import OBSERVATIONS
import requests
from requests import RequestException

from enum import Enum
from pydantic import BaseModel, ValidationError, Field
from typing import List, Optional
from datetime import datetime, timedelta

from transit_odp.common.utils.aws_common import get_s3_bucket_storage

from transit_odp.transmodel.models import BankHolidays
from typing import Tuple, Dict
import copy

logger = logging.getLogger(__name__)


def get_transxchange_schema():
    definition = SchemaDefinition.objects.get(category=SchemaCategory.TXC)
    schema_loader = SchemaLoader(definition, TXC_XSD_PATH)
    return schema_loader.schema


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


class QueuePayloadItem:
    def __init__(self, file_id, check_id, result_id, queue_name):
        self.file_id = file_id
        self.check_id = check_id
        self.result_id = result_id
        self.queue_name = queue_name

    def to_dict(self):
        return {
            "file_id": self.file_id,
            "check_id": self.check_id,
            "result_id": self.result_id,
        }


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


def get_filtered_rows_by_journeys(
    df: pd.DataFrame, journey_mappings: Dict
) -> pd.DataFrame:
    """Apply the filter function for each row"""
    return df[
        df.apply(lambda row: filter_rows_by_journeys(row, journey_mappings), axis=1)
    ]


def get_journey_mappings(df: pd.DataFrame) -> dict:
    return (
        df.groupby(["file_id", "vehicle_journey_code"])["day_of_week"]
        .unique()
        .apply(list)
        .to_dict()
    )


def filter_rows_by_journeys(row: pd.Series, journey_mapping: Dict) -> bool:
    """Filter out row if the date is considered operational and doesnt need an explicit entry into th exceptions table as its operation is covered by the operating profile"""
    date_obj = row["exceptions_date"]
    if date_obj:
        day_of_week = date_obj.strftime("%A")
        operational_days = journey_mapping[
            (row["file_id"], row["vehicle_journey_code"])
        ]
        if row["exceptions_operational"] == True:
            return day_of_week not in operational_days
        return day_of_week in operational_days

    return False


def get_line_description_based_on_direction(row: pd.Series) -> str:
    direction_mapping = {
        "inbound": row["inbound_description"],
        "outbound": row["outbound_description"],
        "clockwise": row["outbound_description"],
        "antiClockwise": row["inbound_description"],
    }
    return direction_mapping.get(row["direction"], "")


def get_vehicle_journey_codes_sorted(
    df_vehicle_journey_operating: pd.DataFrame,
) -> List:
    """
    Get the vehicle journey codes sorted based on the departure time.
    """
    df_vehicle_journey_sorted = df_vehicle_journey_operating.sort_values(
        by=["departure_day_shift", "start_time"]
    )
    df_vehicle_journey_sorted["vehicle_journey_code"] = df_vehicle_journey_sorted[
        "vehicle_journey_code"
    ].astype(str)

    vehicle_journeys = df_vehicle_journey_sorted[
        ["vehicle_journey_code", "vehicle_journey_id"]
    ].drop_duplicates()
    return list(vehicle_journeys.itertuples(index=False, name=None))


def get_df_timetable_visualiser(
    df_vehicle_journey_operating: pd.DataFrame, observations: dict
) -> Tuple[pd.DataFrame, Dict]:
    """
    Get the dataframe containing the list of stops and the timetable details
    with journey code as columns
    """

    if df_vehicle_journey_operating.empty:
        return (df_vehicle_journey_operating, {})

    # Keep the relevant columns of dataframe and remove the duplicates
    columns_to_keep = [
        "common_name",
        "stop_sequence",
        "vehicle_journey_code",
        "departure_time",
        "atco_code",
        "departure_day_shift",
        "start_time",
        "vehicle_journey_id",
        "street",
        "indicator",
        "service_pattern_stop_id",
    ]

    df_vehicle_journey_operating = df_vehicle_journey_operating[columns_to_keep]
    df_vehicle_journey_with_pattern_stop = copy.deepcopy(df_vehicle_journey_operating)
    # drop service pattern stop id column if exists:
    if 'service_pattern_stop_id' in df_vehicle_journey_operating.columns:
        df_vehicle_journey_operating = df_vehicle_journey_operating.drop(
            columns=["service_pattern_stop_id"]
        )

    df_vehicle_journey_operating = df_vehicle_journey_operating.drop_duplicates()

    df_vehicle_journey_operating["key"] = df_vehicle_journey_operating.apply(
        lambda row: f"{row['common_name']}_{row['stop_sequence']}_{row['vehicle_journey_code']}_{row['vehicle_journey_id']}",
        axis=1,
    )
    vehicle_journey_codes_sorted = get_vehicle_journey_codes_sorted(
        df_vehicle_journey_operating
    )
    # Extract the stops based on the stop sequence and departure time
    df_sequence_time: pd.DataFrame = df_vehicle_journey_operating.sort_values(
        ["stop_sequence", "departure_time"]
    )
    df_sequence_time = df_sequence_time[
        [
            "stop_sequence",
            "common_name",
            "street",
            "indicator",
            "atco_code",
        ]
    ]
    df_sequence_time = df_sequence_time.drop_duplicates()
    df_sequence_time["key"] = df_sequence_time.apply(
        lambda row: f"{row['common_name']}_{row['stop_sequence']}",
        axis=1,
    )
    bus_stops = df_sequence_time["common_name"].tolist()
    observation_stops = {}
    stops = {}
    departure_time_data = {}

    for row in df_vehicle_journey_operating.to_dict("records"):
        departure_time_data[row["key"]] = row["departure_time"].strftime("%H:%M")

    stops_journey_code_time_list = []
    for idx, row in enumerate(df_sequence_time.to_dict("records")):
        record = {}
        stops[f"{row['common_name']}_{idx}"] = {
            "atco_code": row["atco_code"],
            "street": row["street"],
            "indicator": row["indicator"],
            "common_name": row["common_name"],
            "stop_seq": row["stop_sequence"],
            "vehicle_journey_id": int(
                df_vehicle_journey_with_pattern_stop.iloc[idx]["vehicle_journey_id"]
            ),
        }
        # if observations are present, add them to the stops
        if observations:
            observation = observations.get(
                df_vehicle_journey_with_pattern_stop.iloc[idx][
                    "service_pattern_stop_id"
                ]
            )
            if observation:
                if f"{row['common_name']}_{idx}" in observation_stops:
                    observation_stops[f"{row['common_name']}_{idx}"][
                        "observations"
                    ].update(observation)
                else:
                    observation_stops.update(
                        {f"{row['common_name']}_{idx}": {"observations": observation}}
                    )
        record["Journey Code"] = bus_stops[idx]
        for (
            journey_code,
            journey_id,
        ) in (
            vehicle_journey_codes_sorted
        ):  # tuple with journey code(cols) and journey id
            key = f"{row['key']}_{journey_code}_{journey_id}"
            record[journey_code] = {
                "departure_time": departure_time_data.get(key, "-"),
                "journey_id": journey_id,
            }
        stops_journey_code_time_list.append(record)

    df_vehicle_journey_operating = pd.DataFrame(stops_journey_code_time_list)
    return (df_vehicle_journey_operating, stops, observation_stops)


def is_vehicle_journey_operating(df_vj, target_date) -> bool:
    df_vj["IsInRange"] = df_vj.apply(
        lambda row: (target_date >= row["start_date"])
        & (target_date <= row["end_date"]),
        axis=1,
    )

    # Step 2: Find out the vehicle journeys which are not operating and lies within start and end date on the target date
    df_non_operating = df_vj[~df_vj["operating_on_working_days"]]
    df_service_nonoperating = df_non_operating[df_non_operating["IsInRange"]]

    if not df_service_nonoperating.empty:
        return False

    # Step 3: Find out the vehicle journeys which are operating and fall outside the operating range
    df_vj = df_vj[df_vj["operating_on_working_days"]]
    if (
        (not df_vj.empty)
        and ((df_vj["IsInRange"] == False).all())
        and (df_non_operating.empty)
    ):
        return False

    return True


def get_non_operating_vj_serviced_org(
    target_date: str, df_serviced_org_working_days: pd.DataFrame
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
    df_serviced_org_working_days = df_serviced_org_working_days.sort_values(
        by=["start_date"]
    )
    vehicle_journey_nonoperating = []

    df_group_vehicle_journey_date = df_serviced_org_working_days.groupby(
        by="vehicle_journey_id"
    )
    vehicle_journey_operating_status = df_group_vehicle_journey_date.apply(
        is_vehicle_journey_operating, target_date
    ).to_dict()

    vehicle_journey_nonoperating = [
        vj for vj, status in vehicle_journey_operating_status.items() if not status
    ]

    return vehicle_journey_nonoperating


def get_vehicle_journeyids_exceptions(
    df_operating_exceptions: pd.DataFrame,
    df_nonoperating_exceptions: pd.DataFrame,
) -> Tuple[List, List]:
    """
    Return the unique vehicle journey which are operating/non-operating and
    combination of both

    In returning tuple, first element contains the list of unique vehicle journey operating,
    second element contains the list of unique vehicle journey non-operating
    """

    # Get all the vehicle journey which are operating on date
    op_exception_vehicle_journey = []
    if (
        not df_operating_exceptions.empty
        and "vehicle_journey_id" in df_operating_exceptions.columns
    ):
        op_exception_vehicle_journey = (
            df_operating_exceptions["vehicle_journey_id"].unique().tolist()
        )

    # Get all the vehicle journey which are not operating on date
    nonop_exception_vehicle_journey = []
    if (
        not df_nonoperating_exceptions.empty
        and "vehicle_journey_id" in df_nonoperating_exceptions.columns
    ):
        nonop_exception_vehicle_journey = (
            df_nonoperating_exceptions["vehicle_journey_id"].unique().tolist()
        )

    return (
        op_exception_vehicle_journey,
        nonop_exception_vehicle_journey,
    )


def get_df_operating_vehicle_journey(
    day_of_week: str,
    df_all_vehicle_journey: pd.DataFrame,
    op_exception_vehicle_journey_ids: List,
    nonop_exception_vehicle_journey: List,
) -> pd.DataFrame:
    """Get the vehicle journeys which are operating on day of the week with any exception
    in the operating and non-operating

    :return: DataFrame
            Returns dataframe containing the valid vehicle journey id
    """

    # Filter the dataframe based on the day of week or in the operating exception
    df_operating_vehicle_journey = df_all_vehicle_journey.loc[
        (df_all_vehicle_journey["day_of_week"] == day_of_week)
        | (
            df_all_vehicle_journey["vehicle_journey_id"].isin(
                op_exception_vehicle_journey_ids
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


def get_initial_vehicle_journeys_df(
    df: pd.DataFrame, line_name: str, target_date: datetime, max_revision_number: int
) -> pd.DataFrame:
    """
    Filter initial vehicle journey dataframe
    """
    return df[
        (df["line_name"] == line_name)
        & (df["revision_number"] == max_revision_number)
        & ((df["end_date"] >= target_date) | (df["end_date"].isna()))
    ]


def fill_missing_journey_codes(df: pd.Series) -> pd.Series:
    """
    Replace empty journey codes with journey id and append a unique identifier
    """
    unique_identifier = "-missing_journey_code"

    # Create a boolean mask for rows where the vehicle journey code is empty
    mask = df["vehicle_journey_code"] == ""
    df.loc[mask, "vehicle_journey_code"] = (
        df.loc[mask, "vehicle_journey_id"].astype(str) + unique_identifier
    )

    return df


def get_updated_columns(df: pd.DataFrame) -> pd.Series:
    """
    Replace column names in the DataFrame where the column name contains '-missing_journey_code'
    with the string '-'.
    """
    return ["-" if "-missing_journey_code" in col else col for col in df.columns]


def create_queue_payload(pending_checks: list) -> dict:
    """
    Create JSON payload as queue items for remote queues for lambdas.
    """
    queue_payload = {}
    for index, check in enumerate(pending_checks):
        payload_item = {
            "file_id": check.transmodel_txcfileattributes.id,
            "check_id": check.checks.id,
            "result_id": check.id,
        }
        queue_name = check.queue_name
        if queue_name not in queue_payload:
            queue_payload[queue_name] = []
        message = {"Id": f"message-{index}", "MessageBody": json.dumps(payload_item)}
        queue_payload[queue_name].append(message)

    return queue_payload


def observation_contents_mapper(observations_list) -> Dict:
    """This function maps the observation list to the observation content
    Args:
        observations_list: list of observations
    Returns:
        requested_observation: dict of observations
    Example output :
        {observation: {"title": observation_content.title,
                        "text":observation_content.text,
                        "resolve": observation_content.resolve
                        }}
    """
    requested_observation = {}
    for observation in observations_list:
        for observation_content in OBSERVATIONS:
            if observation_content.title == observation:
                requested_observation[observation] = {
                    "title": observation_content.title,
                    "text": observation_content.text,
                    "resolve": observation_content.resolve,
                }

    return requested_observation
