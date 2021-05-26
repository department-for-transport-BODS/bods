import pytest

from transit_odp.validate.errors import XMLErrorMessageRenderer

ERRORS = [
    (
        "Element '{http://www.transxchange.org.uk/}TransXChange': No matching global "
        "declaration available for the validation root.",
        "The dataset contains an XML file which couldn't be parsed </br> - "
        "Invalid elements",
    ),
    (
        "Element '{http://www.netex.org.uk/netex}FromDate': '2020-01-01T00:00' "
        "is not a "
        "valid value of the atomic type 'xs:dateTime'.",
        "The dataset contains an XML file which couldn't be parsed </br> - "
        "Invalid values",
    ),
    (
        "Element '{http://www.netex.org.uk/netex}MinimumAge': 'hello' is not a "
        "valid value of the atomic type 'xs:integer'.",
        "The dataset contains an XML file which couldn't be parsed </br> - "
        "Invalid values",
    ),
    (
        "Element '{http://www.netex.org.uk/netex}Blah': This element is not expected.",
        "The dataset contains an XML file which couldn't be parsed </br> - "
        "Invalid elements",
    ),
    (
        "Element 'html': No matching global declaration available for the "
        "validation root.",
        "The dataset contains an XML file which couldn't be parsed </br> - "
        "Invalid elements",
    ),
    (
        "mismatched tag: line 21, column 22",
        "The dataset contains an XML file which couldn't be parsed </br> - "
        "Mismatched tag",
    ),
    (
        "Element '{http://www.netex.org.uk/netex}ParticipantRef': This element is "
        "not expected. Expected is "
        "( {http://www.netex.org.uk/netex}PublicationTimestamp ).",
        "The dataset contains an XML file which couldn't be parsed </br> - "
        "Elements not defined",
    ),
]


@pytest.mark.parametrize("input_msg, expected", ERRORS)
def test_netex_xml_syntax_error_parsing(input_msg, expected):
    renderer = XMLErrorMessageRenderer(input_msg)
    assert renderer.get_message() == expected
