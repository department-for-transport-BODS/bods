import math
from urllib.parse import parse_qs, urlencode


def remove_query_string_param(query_string: str, key: str) -> str:
    """If a query string contains a `key` field remove it."""
    query_params = parse_qs(query_string)
    query_params.pop(key, None)
    query_string = urlencode(query_params, doseq=True)
    return query_string


def round_down(value: float):
    return math.floor(value * 100.0) / 100.0
