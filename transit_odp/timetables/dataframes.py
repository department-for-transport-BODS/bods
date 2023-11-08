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

        items.append(
            {
                "service_code": service_code,
                "start_date": start_datetime,
                "end_date": end_datetime,
                "line_names": [node.text for node in line_names],
            }
        )

    columns = ["service_code", "start_date", "end_date", "line_names"]
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
