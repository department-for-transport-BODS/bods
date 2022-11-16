import pytest

from transit_odp.fares_validator.views.functions import _extract_text
from lxml import etree

TEST_SAMPLE_XML = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <PublicationTimestamp>2119-06-22T13:51:43.044Z</PublicationTimestamp>
    <ParticipantRef>SYS001</ParticipantRef>
    <PublicationRequest version="1.0">
        <RequestTimestamp>2119-06-22T13:51:43.044Z</RequestTimestamp>
        <ParticipantRef>SYS002</ParticipantRef>
        <Description>Request for HCTY Line_16.</Description>
    </PublicationRequest>
</PublicationDelivery>"""

def form_etree_object(source):
    document = etree.parse(source)
    return document

def test_extract_text():
    expected = "sometext" #some text
    doc = form_etree_object(TEST_SAMPLE_XML)
    xpath = "//x:PublicationRequest"
    element = doc.xpath(xpath, namespaces = "http://www.netex.org.uk/netex")
    print("element", element)
    # define fixtures
    # form elements or use from fixtures
    # assert expected value to calculated value
    # assert expected == calculated
