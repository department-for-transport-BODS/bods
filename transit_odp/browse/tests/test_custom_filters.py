
import pytest
from transit_odp.browse.templatetags.custom_filters import round_percentage


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("99.9%","99%"),
        ("80.1%", "80%"),
        ("75.65%", "75%"),
    ],
)
def test_custom_filter(value, expected):
    received = round_percentage(value)
    assert received == expected