""" dataframes.py a collection of utility functions to convert
    TransXChangeDocuments to and from pandas dataframes.
"""

import logging

import pandas as pd

from transit_odp.common.utils.geometry import grid_gemotry_from_str, wsg84_from_str
from transit_odp.common.utils.timestamps import extract_timestamp
from transit_odp.timetables.exceptions import MissingLines
from transit_odp.timetables.transxchange import GRID_LOCATION, WSG84_LOCATION

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
    return pd.DataFrame(items, columns=columns)


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
    # jp1, [js_1....]
    journey_patterns = pd.DataFrame(all_items)
    # Note - 'journey_pattern_id' is not necessarily unique across all
    # services so we make it unique by service_code
    if not journey_patterns.empty:
        journey_patterns["journey_pattern_id"] = journey_patterns[
            "service_code"
        ].str.cat(journey_patterns["journey_pattern_id"], sep="-")

    return journey_patterns


def flexible_journey_patterns_to_dataframe(services):
    all_items = []
    for service in services:
        service_code = service.get_element(["ServiceCode"]).text
        flexible_service = service.get_element_or_none(["FlexibleService"])
        if flexible_service:
            for pattern in flexible_service.get_elements(["FlexibleJourneyPattern"]):
                flexible_zones = pattern.get_elements_or_none(["FlexibleZones"])
                fixed_stop_points = pattern.get_elements_or_none(["FixedStopPoints"])
                stop_points_in_sequence = pattern.get_elements_or_none(
                    ["StopPointsInSequence"]
                )
                stop_point_refs = []

                if flexible_zones:
                    for flexible_zone in flexible_zones:
                        stop_point_refs.extend(
                            [
                                flexible_stop.get_element(["StopPointRef"]).text
                                for flexible_stop in flexible_zone.get_elements(
                                    ["FlexibleStopUsage"]
                                )
                            ]
                        )

                if fixed_stop_points:
                    for fixed_stop_point in fixed_stop_points:
                        stop_point_refs.extend(
                            [
                                fixed_stop_point_stop.get_element(["StopPointRef"]).text
                                for fixed_stop_point_stop in fixed_stop_point.get_elements(
                                    ["FlexibleStopUsage"]
                                )
                            ]
                        )

                if stop_points_in_sequence:
                    for sequence_point in stop_points_in_sequence:
                        stop_point_refs.extend(
                            [
                                sequence_point_stop.get_element(["StopPointRef"]).text
                                for sequence_point_stop in sequence_point.get_elements(
                                    ["FlexibleStopUsage"]
                                )
                            ]
                        )

                    all_items.append(
                        {
                            "service_code": service_code,
                            "journey_pattern_id": pattern["id"],
                            "stop_point_ref": stop_point_refs,
                        }
                    )

    flexible_journey_patterns = pd.DataFrame(all_items)
    if not flexible_journey_patterns.empty:
        flexible_journey_patterns["journey_pattern_id"] = flexible_journey_patterns[
            "service_code"
        ].str.cat(flexible_journey_patterns["journey_pattern_id"], sep="-")

    return flexible_journey_patterns


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

    return pd.concat(dataframes, axis=0, ignore_index=True).set_index(
        ["file_id", "journey_pattern_id", "order"]
    )


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
                    phone_element = booking_arrangement.get_element(["Phone"])
                    tel_national_number = (
                        phone_element.get_element(["TelNationalNumber"]).text
                        if phone_element
                        else None
                    )
                    email = booking_arrangement.get_element(["Email"]).text
                    web_address = booking_arrangement.get_element(["WebAddress"]).text

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
