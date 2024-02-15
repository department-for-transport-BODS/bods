""" dataframes.py a collection of utility functions to convert
    TransXChangeDocuments to and from pandas dataframes.
"""

import logging
import uuid

import pandas as pd

from transit_odp.common.utils.geometry import grid_gemotry_from_str, wsg84_from_str
from transit_odp.common.utils.timestamps import extract_timestamp
from transit_odp.timetables.exceptions import MissingLines
from transit_odp.timetables.transxchange import GRID_LOCATION, WSG84_LOCATION

logger = logging.getLogger(__name__)


def flexible_service_stop_points_dataframe(services):
    stop_points = []
    for service in services:
        service_code = service.get_element(["ServiceCode"]).text
        flexible_services = service.get_elements_or_none(["FlexibleService"])
        if flexible_services:
            for flexible_service in flexible_services:
                for pattern in flexible_service.get_elements(
                    ["FlexibleJourneyPattern"]
                ):
                    flexible_zone = pattern.get_element_or_none("FlexibleZones")
                    if flexible_zone:
                        for flexistopusage in flexible_zone.get_elements(
                            "FlexibleStopUsage"
                        ):
                            atco_code = flexistopusage.get_element("StopPointRef").text
                            stop_points.append(
                                {
                                    "service_code": service_code,
                                    "atco_code": atco_code,
                                    "bus_stop_type": "flexible",
                                    "journey_pattern_id": pattern["id"],
                                }
                            )
                    fixed_stop_points = pattern.get_element_or_none("FixedStopPoints")
                    if fixed_stop_points:
                        for fixed_stop_usage in fixed_stop_points.get_elements(
                            "FixedStopUsage"
                        ):
                            atco_code = fixed_stop_usage.get_element(
                                "StopPointRef"
                            ).text
                            stop_points.append(
                                {
                                    "service_code": service_code,
                                    "atco_code": atco_code,
                                    "bus_stop_type": "fixed_flexible",
                                    "journey_pattern_id": pattern["id"],
                                }
                            )
                    stoppoint_in_sequence = pattern.get_element_or_none(
                        "StopPointsInSequence"
                    )
                    for children in stoppoint_in_sequence.children:
                        bus_stop_type = (
                            "fixed_flexible"
                            if children.localname == "FixedStopUsage"
                            else "flexible"
                        )
                        atco_code = children.get_element_or_none("StopPointRef").text
                        stop_points.append(
                            {
                                "service_code": service_code,
                                "atco_code": atco_code,
                                "bus_stop_type": bus_stop_type,
                                "journey_pattern_id": pattern["id"],
                            }
                        )

    if stop_points:
        columns = ["atco_code", "bus_stop_type", "journey_pattern_id", "service_code"]
        return pd.DataFrame(stop_points, columns=columns)

    return pd.DataFrame()


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
        all_points.append({"atco_code": atco_code})

    return pd.DataFrame(all_points, columns=["atco_code"]).set_index("atco_code")


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
                timing_link_id = link["id"]

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

            all_vechicle_journeys.append(
                {
                    "departure_time": departure_time,
                    "journey_pattern_ref": "-".join([service_ref, journey_pattern_ref]),
                    "line_ref": line_ref,
                    "journey_code": journey_code,
                    "vehicle_journey_code": vehicle_journey_code,
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
                    "departure_time": None,
                    "journey_pattern_ref": "-".join([service_ref, journey_pattern_ref]),
                    "line_ref": line_ref,
                    "journey_code": None,
                    "vehicle_journey_code": vehicle_journey_code,
                }
            )

    return pd.DataFrame(all_vechicle_journeys)


def operating_profile_to_df(operating_profiles):
    serviced_orgs_refs_df = []
    for operating_profile in operating_profiles:
        serviced_organisation_day_type = operating_profile.get_element_or_none(
            ["ServicedOrganisationDayType"]
        )
        if serviced_organisation_day_type:
            days_of_operation = serviced_organisation_day_type.get_element_or_none(
                ["DaysOfOperation"]
            )
            days_of_non_operation = serviced_organisation_day_type.get_element_or_none(
                ["DaysOfNonOperation"]
            )
            if days_of_operation:
                operational = True
                working_days = days_of_operation.get_element("WorkingDays")
            elif days_of_non_operation:
                operational = False
                working_days = days_of_non_operation.get_element("WorkingDays")
            serviced_org_ref = working_days.get_element("ServicedOrganisationRef").text

            serviced_orgs_refs_df.append(
                {"serviced_org_ref": serviced_org_ref, "operational": operational}
            )

    return pd.DataFrame(serviced_orgs_refs_df)


def serviced_organisations_to_dataframe(serviced_organisations):
    serviced_organisations_df = []
    for serviced_organisation in serviced_organisations:
        organisation_code = serviced_organisation.get_element(["OrganisationCode"]).text
        name = serviced_organisation.get_element(["Name"]).text

        serviced_organisations_df.append(
            {
                "serviced_org_ref": organisation_code,
                "name": name,
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
