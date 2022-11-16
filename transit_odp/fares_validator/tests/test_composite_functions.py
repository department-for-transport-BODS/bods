import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    check_composite_frame_valid_between,
)


@pytest.mark.parametrize(
    ("valid_between", "from_date", "expected"),
    [(True, True, False), (False, False, True), (True, False, True)],
)
def test_composite_frame_valid_between(valid_between, from_date, expected):
    actual = False
    valid_between_with_child = """
    <ValidBetween>
        <FromDate>442914</FromDate>
    </ValidBetween>
    """

    valid_between_without_child = """
    <ValidBetween>
    </ValidBetween>
    """

    composite_frames = """
    <dataObjects>
        <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
            {0}
        </CompositeFrame>
    </dataObjects>
    """

    if valid_between:
        if from_date:
            xml = composite_frames.format(valid_between_with_child)
        else:
            xml = composite_frames.format(valid_between_without_child)
    else:
        xml = composite_frames.format("")

    netex_xml = etree.fromstring(xml.encode("utf-8"))
    element_list = []
    element_list.append(netex_xml)
    response = check_composite_frame_valid_between("", element_list)
    print("response ", response)
    if len(response):
        actual = True
    assert actual == expected
