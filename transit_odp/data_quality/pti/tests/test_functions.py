from unittest.mock import Mock

import pytest
from dateutil import parser
from freezegun import freeze_time
from lxml.etree import Element

from transit_odp.data_quality.pti.functions import (
    cast_to_bool,
    cast_to_date,
    contains_date,
    has_prohibited_chars,
    is_member_of,
    today,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([Mock(spec=Element, text="true")], True),
        ([Mock(spec=Element, text="false")], False),
        (Mock(spec=Element, text="true"), True),
        (Mock(spec=Element, text="false"), False),
        (["true"], True),
        (["false"], False),
        ("true", True),
        ("false", False),
        (Mock(spec=Element), False),
    ],
)
def test_cast_to_bool(value, expected):
    context = Mock()
    actual = cast_to_bool(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            [Mock(spec=Element, text="2015-01-01")],
            parser.parse("2015-01-01").timestamp(),
        ),
        (
            Mock(spec=Element, text="2015-01-01"),
            parser.parse("2015-01-01").timestamp(),
        ),
        ("2015-01-01", parser.parse("2015-01-01").timestamp()),
    ],
)
def test_cast_to_date(value, expected):
    context = Mock()
    actual = cast_to_date(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    ("value", "list_items", "expected"),
    [
        ([Mock(spec=Element, text="other")], ("one", "two"), False),
        ([Mock(spec=Element, text="one")], ("one", "two"), True),
        (Mock(spec=Element, text="other"), ("one", "two"), False),
        (Mock(spec=Element, text="one"), ("one", "two"), True),
        ("other", ("one", "two"), False),
        ("one", ("one", "two"), True),
        ("", ("one", "two"), False),
        (Mock(spec=Element), ("one", "two"), False),
    ],
)
def test_is_member_of(value, list_items, expected):
    context = Mock()
    actual = is_member_of(context, value, *list_items)
    assert actual == expected


@freeze_time("2020-02-02")
def test_today():
    context = Mock()
    actual = today(context)
    assert actual == parser.parse("2020-02-02").timestamp()


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([Mock(spec=Element, text="hello,world")], True),
        ([Mock(spec=Element, text="hello world")], False),
        (Mock(spec=Element, text="hello,world"), True),
        (Mock(spec=Element, text="false"), False),
        (["hello,world"], True),
        (["false"], False),
        ("hello,world", True),
        ("false", False),
        (Mock(spec=Element), False),
    ],
)
def test_has_prohibited_chars(value, expected):
    context = Mock()
    actual = has_prohibited_chars(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([Mock(spec=Element, text="world")], False),
        ([Mock(spec=Element, text="2020-12-01 world")], True),
        (Mock(spec=Element, text="hello,world"), False),
        (Mock(spec=Element, text="12-01 world"), True),
        (["hello,world"], False),
        (["01/08/21 hello world"], True),
        ("hello,world", False),
        ("01/08/21 hello world", True),
        ("15 hello world", False),
        (Mock(spec=Element), False),
    ],
)
def test_contains_date(value, expected):
    context = Mock()
    actual = contains_date(context, value)
    assert actual == expected
