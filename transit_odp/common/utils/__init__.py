import hashlib
import math
from typing import Union
from urllib.parse import parse_qs, urlencode, urlparse

from django_hosts import reverse


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


def reverse_path(*args, **kwargs) -> str:
    """
    django_hosts reverse helper function
    does a reverse but only return the path info
    args and kwargs are the same as django_hosts.reverse
    returns path string of resource
    """
    full_url = reverse(*args, **kwargs)
    parsed_url = urlparse(full_url)
    return parsed_url.path


def sha1sum(content: Union[bytes, bytearray, memoryview]) -> str:
    """
    Takes the sha1 of a string and returns a hex string
    """
    return hashlib.sha1(content).hexdigest()
