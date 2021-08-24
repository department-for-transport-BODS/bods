import math
from urllib.parse import parse_qs, urlencode


def remove_query_string_param(query_string: str, key: str) -> str:
    """If a query string contains a `key` field remove it."""
    query_params = parse_qs(query_string)
    query_params.pop(key, None)
    query_string = urlencode(query_params, doseq=True)
    return query_string


def get_dataset_type_from_path_info(path_info: str) -> str:
    """Update the raw api based on `path_info`"""
    dataset_type = ""
    if "/datafeed" in path_info:
        dataset_type = "SIRI VM"
    elif "/gtfsrtdatafeed" in path_info:
        dataset_type = "GTFS RT"
    elif "/fares" in path_info:
        dataset_type = "Fares"
    elif "/dataset" in path_info:
        dataset_type = "Timetable"
    else:
        return dataset_type
    return dataset_type


def round_down(value: float):
    return math.floor(value * 100.0) / 100.0
