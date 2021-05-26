import pytest
from lxml import etree

from transit_odp.common.xmlelements import XMLElement
from transit_odp.common.xmlelements.exceptions import (
    NoElement,
    ParentDoesNotExist,
    TooManyElements,
    XMLAttributeError,
)

TEST_XML = """<PublicationDelivery version="1.1">
    <PublicationTimestamp>2119-06-22T13:51:43.044Z</PublicationTimestamp>
    <ParticipantRef>SYS001</ParticipantRef>
    <PublicationRequest version="1.0">
        <RequestTimestamp>2119-06-22T13:51:43.044Z</RequestTimestamp>
        <ParticipantRef>SYS002</ParticipantRef>
        <Description>Request for HCTY Line_16.</Description>
    </PublicationRequest>
    <Description>Example  of simple point to point fares</Description>
    <dataObjects>
        <CompositeFrame>composite_frame</CompositeFrame>
        <CompositeFrame>composite_frame2</CompositeFrame>
    </dataObjects>
    </PublicationDelivery>
    """


@pytest.fixture
def xmlelement():
    return XMLElement(etree.fromstring(TEST_XML))


def test_text_property(xmlelement):
    expected = "SYS001"
    actual = xmlelement.get_element("ParticipantRef").text
    assert expected == actual


def test_xpath_list(xmlelement):
    expected = "SYS002"
    actual = xmlelement.get_element(["PublicationRequest", "ParticipantRef"]).text
    assert expected == actual


def test_children_property(xmlelement):
    publication_request = xmlelement.get_element("PublicationRequest")
    expected = [element.text for element in publication_request._element.getchildren()]
    actual = [element.text for element in publication_request.children]
    assert expected == actual


def test_parent_property(xmlelement):
    publication_request = xmlelement.get_element("PublicationRequest")
    expected = xmlelement
    actual = publication_request.parent
    assert expected == actual


def test_parent_does_not_exist(xmlelement):
    with pytest.raises(ParentDoesNotExist) as exc_info:
        xmlelement.parent

    expected = "'PublicationDelivery' has no parent element"
    assert str(exc_info.value) == expected


def test_localname(xmlelement):
    publication_request = xmlelement.get_element("PublicationRequest")
    expected = "PublicationRequest"
    actual = publication_request.localname
    assert expected == actual


def test_no_child_element(xmlelement):
    xpath = "ThisDoesNotExist"
    with pytest.raises(NoElement) as exc_info:
        xmlelement.get_element(xpath)

    assert str(exc_info.value) == f"PublicationDelivery has no xpath {xpath!r}"


def test_too_many_children(xmlelement):
    xpath = ["dataObjects", "CompositeFrame"]
    with pytest.raises(TooManyElements) as exc_info:
        xmlelement.get_element(xpath)

    assert str(exc_info.value) == "More than 1 element found"


def test_get_element_attribute(xmlelement):
    expected = "1.1"
    actual = xmlelement["version"]
    assert expected == actual


def test_get_element_attribute_exception(xmlelement):
    with pytest.raises(XMLAttributeError) as exc_info:
        xmlelement["does_not_exist"]

    expected = "'PublicationDelivery' has no attribute 'does_not_exist'"
    actual = str(exc_info.value)
    assert expected == actual


def test_find_anywhere(xmlelement):
    actual = xmlelement.find_anywhere("CompositeFrame")
    assert len(actual) == 2
    assert actual[0].localname == "CompositeFrame"
    assert actual[-1].text == "composite_frame2"
