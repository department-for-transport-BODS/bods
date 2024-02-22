""" dataframes.py a collection of utility functions to convert
    TransXChangeDocuments to and from pandas dataframes.
"""

import logging

import pandas as pd

from transit_odp.common.utils.geometry import grid_gemotry_from_str, wsg84_from_str
from transit_odp.common.utils.timestamps import extract_timestamp
from transit_odp.timetables.exceptions import MissingLines
from transit_odp.timetables.transxchange import GRID_LOCATION, WSG84_LOCATION
from transit_odp.pipelines.pipelines.dataset_etl.utils.dataframes import (
    db_bank_holidays_to_df,
)
from datetime import datetime, timedelta

from transit_odp.transmodel.models import BankHolidays

logger = logging.getLogger(__name__)


def services_to_dataframe(services):
    """Convert a TransXChange Service XMLElement to a pandas DataFrame"""
    items = []
    for service in services:
        service_code = service.get_element("ServiceCode").text
        start_date = service.get_element(["OperatingPeriod", "StartDate"]).text
        end_date = service.get_element_or_none(["OperatingPeriod", "EndDate"])
        flexible_service = service.get_element_or_none(["FlexibleService"])
        if end_date:
            end_date = end_date.text
        line_names = service.get_elements(["Lines", "Line", "LineName"])

        if len(line_names) < 1:
            raise MissingLines(service=service_code)

        start_datetime = extract_timestamp(start_date)
        end_datetime = extract_timestamp(end_date)
        # TODO start and end dates can be stored as Date in DB rather than DateTime.
        end_datetime = (
            end_datetime.replace(hour=23, minute=59) if end_datetime else None
        )
        service_type = "standard"

        if flexible_service:
            service_type = "flexible"

        items.append(
            {
                "service_code": service_code,
                "start_date": start_datetime,
                "end_date": end_datetime,
                "line_names": [node.text for node in line_names],
                "service_type": service_type,
            }
        )

    columns = ["service_code", "start_date", "end_date", "line_names", "service_type"]
    service_df = pd.DataFrame(items, columns=columns)
    for datetime_column_name in ["start_date", "end_date"]:
        service_df[datetime_column_name].fillna(pd.to_datetime("NaT"), inplace=True)
    return service_df


def stop_point_refs_to_dataframe(stop_point_refs):
    all_points = []
    for ref in stop_point_refs:
        atco_code = ref.get_element(["StopPointRef"]).text
        common_name = ref.get_element(["CommonName"]).text
        all_points.append({"atco_code": atco_code, "common_name": common_name})

    return pd.DataFrame(all_points, columns=["atco_code", "common_name"]).set_index(
        "atco_code"
    )


def provisional_stops_to_dataframe(stops, system=None):
    stop_points = []
    for stop in stops:
        atco_code = stop.get_element(["AtcoCode"]).text
        location = stop.get_element(["Place", "Location"])

        if system is None or system.lower() == GRID_LOCATION.lower():
            easting = location.get_element(["Translation", "Easting"]).text
            northing = location.get_element(["Translation", "Northing"]).text
            geometry = (
                grid_gemotry_from_str(easting, northing)
                if easting and northing
                else None
            )

        elif system.lower() == WSG84_LOCATION.lower():
            latitude = location.get_element(["Translation", "Latitude"]).text
            longitude = location.get_element(["Translation", "Longitude"]).text
            geometry = (
                wsg84_from_str(longitude, latitude) if latitude and longitude else None
            )
        locality_id = stop.get_element(["Place", "NptgLocalityRef"]).text
        stop_points.append(
            {"atco_code": atco_code, "geometry": geometry, "locality": locality_id}
        )

    columns = ["atco_code", "geometry", "locality"]
    return pd.DataFrame(stop_points, columns=columns).set_index("atco_code")


def journey_patterns_to_dataframe(services):
    all_items = []
    for service in services:
        service_code = service.get_element(["ServiceCode"]).text
        standard_service = service.get_element_or_none(["StandardService"])
        flexible_service = service.get_element_or_none(["FlexibleService"])

        if standard_service:
            for pattern in standard_service.get_elements(["JourneyPattern"]):
                section_refs = pattern.get_elements(["JourneyPatternSectionRefs"])
                direction = pattern.get_element_or_none(["Direction"])
                all_items.append(
                    {
                        "service_code": service_code,
                        "journey_pattern_id": pattern["id"],
                        "direction": direction.text if direction is not None else "",
                        "jp_section_refs": [ref.text for ref in section_refs],
                    }
                )

        if flexible_service:
            for pattern in flexible_service.get_elements(["FlexibleJourneyPattern"]):
                direction = pattern.get_element_or_none(["Direction"])
                all_items.append(
                    {
                        "service_code": service_code,
                        "journey_pattern_id": pattern["id"],
                        "direction": direction.text if direction is not None else "",
                        "jp_section_refs": [],
                    }
                )

    journey_patterns = pd.DataFrame(all_items)
    # Note - 'journey_pattern_id' is not necessarily unique across all
    # services so we make it unique by service_code
    if not journey_patterns.empty:
        journey_patterns["journey_pattern_id"] = journey_patterns[
            "service_code"
        ].str.cat(journey_patterns["journey_pattern_id"], sep="-")

    return journey_patterns


def journey_pattern_section_from_journey_pattern(df: pd.DataFrame):
    dataframes = []
    # The journey_patterns DataFrame has a multiindex
    for (file_id, journey_pattern_id), row in df.iterrows():
        for i, ref in enumerate(row["jp_section_refs"]):
            dataframes.append(
                pd.DataFrame(
                    [
                        {
                            "file_id": file_id,
                            "journey_pattern_id": journey_pattern_id,
                            "jp_section_ref": ref,
                            "order": i,
                        }
                    ]
                )
            )

    if dataframes:
        return pd.concat(dataframes, axis=0, ignore_index=True).set_index(
            ["file_id", "journey_pattern_id", "order"]
        )
    else:
        return pd.DataFrame()


def journey_pattern_sections_to_dataframe(sections):
    all_links = []
    if sections is not None:
        for section in sections:
            id_ = section["id"]
            links = section.get_elements(["JourneyPatternTimingLink"])
            for order, link in enumerate(links):
                from_stop_ref = link.get_element(["From", "StopPointRef"]).text
                to_stop_ref = link.get_element(["To", "StopPointRef"]).text
                to_stop_timing_status = link.get_element_or_none(["To", "TimingStatus"])
                is_timing_status = False
                if to_stop_timing_status and to_stop_timing_status.text in [
                    "principalTimingPoint",
                    "PTP",
                ]:
                    is_timing_status = True
                timing_link_id = link["id"]

                run_time = pd.NaT
                element_run_time = link.get_element_or_none(["RunTime"])
                if element_run_time:
                    run_time = pd.to_timedelta(element_run_time.text)
                element_wait_time = link.get_element_or_none(["To", "WaitTime"])
                wait_time = pd.NaT
                if element_wait_time:
                    wait_time = pd.to_timedelta(element_wait_time.text)

                route_link_ref = link.get_element_or_none(["RouteLinkRef"])
                if route_link_ref:
                    route_link_ref = route_link_ref.text
                else:
                    route_link_ref = hash((from_stop_ref, to_stop_ref))

                all_links.append(
                    {
                        "jp_section_id": id_,
                        "jp_timing_link_id": timing_link_id,
                        "route_link_ref": route_link_ref,
                        "order": order,
                        "from_stop_ref": from_stop_ref,
                        "to_stop_ref": to_stop_ref,
                        "is_timing_status": is_timing_status,
                        "run_time": run_time,
                        "wait_time": wait_time,
                    }
                )
    timing_links = pd.DataFrame(all_links)
    return timing_links


def vehicle_journeys_to_dataframe(
    standard_vehicle_journeys, flexible_vechicle_journeys
):
    all_vechicle_journeys = []
    if standard_vehicle_journeys is not None:
        for vehicle_journey in standard_vehicle_journeys:
            departure_time = vehicle_journey.get_element(["DepartureTime"]).text
            journey_pattern_ref_element = vehicle_journey.get_element_or_none(
                ["JourneyPatternRef"]
            )
            journey_pattern_ref = ""
            if journey_pattern_ref_element:
                journey_pattern_ref = journey_pattern_ref_element.text
            line_ref = vehicle_journey.get_element(["LineRef"]).text
            journey_code_element = vehicle_journey.get_element_or_none(
                ["Operational", "TicketMachine", "JourneyCode"]
            )
            journey_code = ""
            if journey_code_element:
                journey_code = journey_code_element.text

            vehicle_journey_code = vehicle_journey.get_element(
                ["VehicleJourneyCode"]
            ).text
            service_ref = vehicle_journey.get_element(["ServiceRef"]).text
            departure_day_shift = False
            departure_day_shift_element = vehicle_journey.get_element_or_none(
                ["DepartureDayShift"]
            )

            if departure_day_shift_element:
                departure_day_shift = True

            vj_timing_links = vehicle_journey.get_elements_or_none(
                ["VehicleJourneyTimingLink"]
            )

            if vj_timing_links:
                for links in vj_timing_links:
                    timing_link_ref = links.get_element(
                        ["JourneyPatternTimingLinkRef"]
                    ).text
                    run_time = pd.to_timedelta(links.get_element(["RunTime"]).text)

                    all_vechicle_journeys.append(
                        {
                            "service_code": service_ref,
                            "departure_time": departure_time,
                            "journey_pattern_ref": "-".join(
                                [service_ref, journey_pattern_ref]
                            ),
                            "line_ref": line_ref,
                            "journey_code": journey_code,
                            "vehicle_journey_code": vehicle_journey_code,
                            "timing_link_ref": timing_link_ref,
                            "run_time": run_time,
                            "departure_day_shift": departure_day_shift,
                        }
                    )

            else:
                all_vechicle_journeys.append(
                    {
                        "service_code": service_ref,
                        "departure_time": departure_time,
                        "journey_pattern_ref": "-".join(
                            [service_ref, journey_pattern_ref]
                        ),
                        "line_ref": line_ref,
                        "journey_code": journey_code,
                        "vehicle_journey_code": vehicle_journey_code,
                        "timing_link_ref": None,
                        "run_time": pd.NaT,
                        "departure_day_shift": departure_day_shift,
                    }
                )

    if flexible_vechicle_journeys is not None:
        for vehicle_journey in flexible_vechicle_journeys:
            line_ref = vehicle_journey.get_element(["LineRef"]).text
            journey_pattern_ref = vehicle_journey.get_element(
                ["JourneyPatternRef"]
            ).text
            vehicle_journey_code = vehicle_journey.get_element(
                ["VehicleJourneyCode"]
            ).text
            service_ref = vehicle_journey.get_element(["ServiceRef"]).text

            all_vechicle_journeys.append(
                {
                    "service_code": service_ref,
                    "departure_time": None,
                    "journey_pattern_ref": "-".join([service_ref, journey_pattern_ref]),
                    "line_ref": line_ref,
                    "journey_code": None,
                    "vehicle_journey_code": vehicle_journey_code,
                    "timing_link_ref": None,
                    "run_time": pd.NaT,
                    "departure_day_shift": False,
                }
            )

    return pd.DataFrame(all_vechicle_journeys)


def flexible_operation_period_to_dataframe(flexible_vechicle_journeys):
    flexible_operation_periods = []
    if flexible_vechicle_journeys is not None:
        for vehicle_journey in flexible_vechicle_journeys:
            vehicle_journey_code = vehicle_journey.get_element(
                ["VehicleJourneyCode"]
            ).text
            flexible_service_times = vehicle_journey.get_element_or_none(
                ["FlexibleServiceTimes"]
            )
            found_service_period = False
            if flexible_service_times:
                service_periods = flexible_service_times.get_elements_or_none(
                    ["ServicePeriod"]
                )

                for service_period in (
                    service_periods if service_periods is not None else []
                ):
                    found_service_period = True
                    start_time = service_period.get_element_or_none(["StartTime"])
                    end_time = service_period.get_element_or_none(["EndTime"])
                    flexible_operation_periods.append(
                        {
                            "vehicle_journey_code": vehicle_journey_code,
                            "start_time": start_time.text
                            if start_time is not None
                            else None,
                            "end_time": end_time.text if end_time is not None else None,
                        }
                    )

            if not found_service_period:
                flexible_operation_periods.append(
                    {
                        "vehicle_journey_code": vehicle_journey_code,
                        "start_time": None,
                        "end_time": None,
                    }
                )

    return pd.DataFrame(flexible_operation_periods)


def get_operating_profile_with_exception(
    operating_profile,
    date=None,
    exceptions_operational=False,
    is_exceptions=False,
):
    operating_profile = {
        "service_code": operating_profile["service_code"],
        "vehicle_journey_code": operating_profile["vehicle_journey_code"],
        "serviced_org_ref": operating_profile["serviced_org_ref"],
        "operational": operating_profile["operational"],
        "day_of_week": operating_profile["day_of_week"],
        "exceptions_operational": None,
        "exceptions_date": None,
    }

    if is_exceptions:
        operating_profile["exceptions_operational"] = exceptions_operational
        if date:
            operating_profile["exceptions_date"] = date

    return operating_profile


def get_operating_profiles_for_all_exceptions(
    operating_profile,
    operations=None,
    df_bank_holidays_from_db=pd.DataFrame(),
    is_bank_holiday_exception=False,
    is_special_operation=False,
    is_days_of_operation=False,
):
    operating_profile_list = []

    if is_bank_holiday_exception:
        for holiday in operations.children:
            date = None
            no_bank_holidays = False
            if holiday.localname == "OtherPublicHoliday":
                date = datetime.strptime(
                    holiday.get_element(["Date"]).text, "%Y-%m-%d"
                ).date()
            else:
                filtered_df = df_bank_holidays_from_db.loc[
                    df_bank_holidays_from_db["txc_element"] == holiday.localname,
                    "date",
                ]

                if not filtered_df.empty:
                    date = filtered_df.values[0]
                else:
                    no_bank_holidays = True
            if not no_bank_holidays:
                operating_profile_list.append(
                    get_operating_profile_with_exception(
                        operating_profile,
                        date,
                        is_days_of_operation,
                        is_exceptions=True,
                    )
                )

    elif is_special_operation:
        if operations:
            date_range = operations.get_elements_or_none(["DateRange"])
            for range in date_range:
                start_date = datetime.strptime(
                    range.get_element(["StartDate"]).text, "%Y-%m-%d"
                ).date()
                end_date = datetime.strptime(
                    range.get_element(["EndDate"]).text, "%Y-%m-%d"
                ).date()

                while start_date <= end_date:
                    operating_profile_list.append(
                        get_operating_profile_with_exception(
                            operating_profile,
                            start_date,
                            is_days_of_operation,
                            is_exceptions=True,
                        )
                    )
                    start_date = start_date + timedelta(days=1)
    else:
        operating_profile_list.append(
            get_operating_profile_with_exception(operating_profile)
        )

    return operating_profile_list


def populate_operating_profiles(operating_profiles, vehicle_journey_code, service_ref):
    operating_profile_list = []
    serviced_org_refs = []
    days_of_week = ""
    operational = ""
    serviced_organisation_day_type = operating_profiles.get_element_or_none(
        ["ServicedOrganisationDayType"]
    )
    regular_day_type = operating_profiles.get_element_or_none(["RegularDayType"])
    special_days_operation = operating_profiles.get_element_or_none(
        ["SpecialDaysOperation"]
    )
    bank_holiday_operation = operating_profiles.get_element_or_none(
        ["BankHolidayOperation"]
    )

    df_bank_holidays_from_db = db_bank_holidays_to_df(["txc_element", "date"])

    current_year = datetime.today().year

    df_bank_holidays_from_db = df_bank_holidays_from_db[
        df_bank_holidays_from_db["date"].apply(lambda x: x.year) == current_year
    ]

    if regular_day_type:
        days_of_week_elements = regular_day_type.get_element_or_none(["DaysOfWeek"])
        days_of_week = (
            [day.localname for day in days_of_week_elements.children]
            if days_of_week_elements
            else ""
        )

    operating_profile_obj = {
        "service_code": service_ref,
        "vehicle_journey_code": vehicle_journey_code,
        "serviced_org_ref": serviced_org_refs,
        "day_of_week": days_of_week,
        "operational": operational,
    }

    if serviced_organisation_day_type:
        days_of_operation = serviced_organisation_day_type.get_element_or_none(
            ["DaysOfOperation"]
        )
        days_of_non_operation = serviced_organisation_day_type.get_element_or_none(
            ["DaysOfNonOperation"]
        )
        if days_of_operation:
            operational = True
            serviced_orgs_working_days = days_of_operation.get_element("WorkingDays")
        elif days_of_non_operation:
            operational = False
            serviced_orgs_working_days = days_of_non_operation.get_element(
                "WorkingDays"
            )
        serviced_org_ref_elements = serviced_orgs_working_days.get_elements(
            "ServicedOrganisationRef"
        )
        serviced_org_refs = [
            serviced_org_ref_element.text
            for serviced_org_ref_element in serviced_org_ref_elements
        ]
        operating_profile_obj["serviced_org_ref"] = serviced_org_refs
        operating_profile_obj["operational"] = operational

    if special_days_operation:
        days_of_operation = special_days_operation.get_element_or_none(
            ["DaysOfOperation"]
        )
        days_of_non_operation = special_days_operation.get_element_or_none(
            ["DaysOfNonOperation"]
        )

        if days_of_operation:
            operating_profile_list.extend(
                get_operating_profiles_for_all_exceptions(
                    operating_profile_obj,
                    days_of_operation,
                    df_bank_holidays_from_db,
                    is_bank_holiday_exception=False,
                    is_special_operation=True,
                    is_days_of_operation=True,
                )
            )

        if days_of_non_operation:
            operating_profile_list.extend(
                get_operating_profiles_for_all_exceptions(
                    operating_profile_obj,
                    days_of_non_operation,
                    df_bank_holidays_from_db,
                    is_bank_holiday_exception=False,
                    is_special_operation=True,
                    is_days_of_operation=False,
                )
            )

    if bank_holiday_operation:
        days_of_operation = bank_holiday_operation.get_element_or_none(
            ["DaysOfOperation"]
        )
        days_of_non_operation = bank_holiday_operation.get_element_or_none(
            ["DaysOfNonOperation"]
        )

        if days_of_operation:
            operating_profile_list.extend(
                get_operating_profiles_for_all_exceptions(
                    operating_profile_obj,
                    days_of_operation,
                    df_bank_holidays_from_db,
                    is_bank_holiday_exception=True,
                    is_special_operation=False,
                    is_days_of_operation=True,
                )
            )

        if days_of_non_operation:
            operating_profile_list.extend(
                get_operating_profiles_for_all_exceptions(
                    operating_profile_obj,
                    days_of_non_operation,
                    df_bank_holidays_from_db,
                    is_bank_holiday_exception=True,
                    is_special_operation=False,
                    is_days_of_operation=False,
                )
            )

    if not special_days_operation or not bank_holiday_operation:
        operating_profile_list.extend(
            get_operating_profiles_for_all_exceptions(operating_profile_obj)
        )

    return operating_profile_list


def operating_profiles_to_dataframe(vehicle_journeys, services):
    operating_profile_list = []
    for vehicle_journey in vehicle_journeys:
        vehicle_journey_code = vehicle_journey.get_element(["VehicleJourneyCode"]).text
        service_ref = vehicle_journey.get_element(["ServiceRef"]).text
        operating_profile_vehicle_journey = vehicle_journey.get_element_or_none(
            ["OperatingProfile"]
        )
        if operating_profile_vehicle_journey:
            operating_profile = operating_profile_vehicle_journey
        else:
            for service in services:
                service_code = service.get_element(["ServiceCode"]).text
                if service_code == service_ref:
                    operating_profile = service.get_element_or_none(
                        ["OperatingProfile"]
                    )
        if operating_profile:
            operating_profiles = populate_operating_profiles(
                operating_profile, vehicle_journey_code, service_ref
            )
            operating_profile_list.extend(operating_profiles)

    operating_profile_df = pd.DataFrame(operating_profile_list)
    operating_profile_df = operating_profile_df.explode("day_of_week")
    operating_profile_df = operating_profile_df.explode("serviced_org_ref")
    operating_profile_df.drop_duplicates(inplace=True)
    operating_profile_df.reset_index(drop=True, inplace=True)

    return operating_profile_df


def serviced_organisations_to_dataframe(serviced_organisations):
    serviced_organisations_df = []
    for serviced_organisation in serviced_organisations:
        organisation_code = serviced_organisation.get_element(["OrganisationCode"]).text
        name = serviced_organisation.get_element(["Name"]).text
        working_days = serviced_organisation.get_element(["WorkingDays"])

        if working_days:
            date_ranges = working_days.get_elements(["DateRange"])
            for date_range in date_ranges:
                serviced_organisations_df.append(
                    {
                        "serviced_org_ref": organisation_code,
                        "name": name,
                        "start_date": date_range.get_element(["StartDate"]).text,
                        "end_date": date_range.get_element(["EndDate"]).text,
                    }
                )

    return pd.DataFrame(serviced_organisations_df)


def booking_arrangements_to_dataframe(services):
    booking_arrangement_props = []
    for service in services:
        flexible_service = service.get_element_or_none(["FlexibleService"])

        if flexible_service:
            service_code = service.get_element(["ServiceCode"]).text
            flexible_journey_patterns = flexible_service.get_elements(
                ["FlexibleJourneyPattern"]
            )

            for flexible_journey_pattern in flexible_journey_patterns:
                booking_arrangements = flexible_journey_pattern.get_elements(
                    ["BookingArrangements"]
                )

                for booking_arrangement in booking_arrangements:
                    description = booking_arrangement.get_element(["Description"]).text
                    phone_element = booking_arrangement.get_element_or_none(["Phone"])
                    tel_national_number = (
                        phone_element.get_element(["TelNationalNumber"]).text
                        if phone_element
                        else None
                    )
                    email_element = booking_arrangement.get_element_or_none(["Email"])
                    email = None
                    if email_element:
                        email = email_element.text

                    web_address_element = booking_arrangement.get_element_or_none(
                        ["WebAddress"]
                    )
                    web_address = None
                    if web_address_element:
                        web_address = web_address_element.text

                    booking_arrangement_props.append(
                        {
                            "service_code": service_code,
                            "description": description,
                            "tel_national_number": tel_national_number,
                            "email": email,
                            "web_address": web_address,
                        }
                    )
    booking_arrangements_df = pd.DataFrame(booking_arrangement_props)

    if not booking_arrangements_df.empty:
        columns = [
            "service_code",
            "description",
            "tel_national_number",
            "email",
            "web_address",
        ]
        return pd.DataFrame(booking_arrangements_df, columns=columns)
    return booking_arrangements_df
