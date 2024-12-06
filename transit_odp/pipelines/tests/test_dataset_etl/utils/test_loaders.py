import pytest
from transit_odp.pipelines.pipelines.dataset_etl.utils.loaders import (
    get_line_name_from_line_ref,
)


@pytest.mark.parametrize(
    "line_ref, expected",
    [
        ("line:ref:12345", "12345"),
        ("line:ref:", "ref"),
        ("line:12345", "12345"),
        ("12345", "12345"),
        (":12345", "12345"),
        ("line::12345", "12345"),
        ("line:ref:12345:", "12345"),
        ("line:ref::", ""),
        (":", ""),
        ("", None),
    ],
)
def test_get_line_name_from_line_ref(line_ref, expected):
    assert get_line_name_from_line_ref(line_ref) == expected
