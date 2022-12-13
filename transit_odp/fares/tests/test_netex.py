import datetime

import pytest
from dateutil.parser import parse as parse_datetime_str

from transit_odp.fares.netex import NeTExDocument, get_documents_from_file
from transit_odp.fares.tests.conftest import FIXTURES


def test_get_netex_document_from_zip_file():
    expected = []
    sample_files = ["sample1.xml", "sample2.xml"]
    for sample in sample_files:
        netex_filepath = str(FIXTURES.joinpath(sample))
        with open(netex_filepath, "rb") as f:
            expected.append(NeTExDocument(f))

    zip_filepath = str(FIXTURES.joinpath("sample.zip"))
    with open(zip_filepath, "rb") as f:
        actual = get_documents_from_file(f)

    assert len(expected) == len(actual)

    # if files are the same then RequestTimestamp should be equal
    xpath = ["PublicationRequest", "RequestTimestamp"]
    expected_timestamp = expected[0].get_element(xpath).text
    actual_timestamp = actual[0].get_element(xpath).text
    assert expected_timestamp == actual_timestamp


def test_get_netex_document_from_file():
    fullpath = FIXTURES.joinpath("sample1.xml")
    with open(fullpath, "rb") as f:
        actual = get_documents_from_file(f)

    assert len(actual) == 1
    xpath = ["PublicationRequest", "RequestTimestamp"]
    expected_timestamp = "2119-06-22T13:51:43.044Z"
    assert actual[0].get_element(xpath).text == expected_timestamp


def test_xpath_list(netexelement):
    xpath = ["PublicationRequest", "ParticipantRef"]
    expected = "SYS002"
    actual = netexelement.xpath(xpath)[0].text
    assert expected == actual
    assert netexelement["version"] == "1.1"
    assert netexelement.xpath("ParticipantRef")[0].text == "SYS001"


def test_xpath_str(netexelement):
    xpath = "ParticipantRef"
    expected = "SYS001"
    actual = netexelement.xpath(xpath)[0].text
    assert expected == actual
    assert netexelement["version"] == "1.1"


def test_get_fare_zones(netexdocument):
    actual = netexdocument.fare_zones
    assert len(actual) == 8
    assert actual[0].localname == "FareZone"


def test_get_lines(netexdocument):
    actual = netexdocument.lines
    assert len(actual) == 1
    assert actual[0].localname == "Line"
    assert actual[0]["id"] == "16"
    assert actual[0].get_element("Name").text == "Connexions Buses 16"


def test_get_user_profiles(netexdocument):
    actual = netexdocument.user_profiles
    assert len(actual) == 4
    assert actual[0].localname == "UserProfile"
    assert actual[0]["id"] == "fxc:adult"


def test_get_sales_offer_packages(netexdocument):
    actual = netexdocument.sales_offer_packages
    assert len(actual) == 1
    assert actual[0].localname == "SalesOfferPackage"


def test_get_netex_version(netexdocument):
    actual = netexdocument.get_netex_version()
    expected = "1.1"
    assert expected == actual


def test_get_xml_file_name(netexdocument):
    actual = netexdocument.get_xml_file_name()
    expected = "/app/transit_odp/fares/tests/fixtures/sample1"
    assert expected == actual


def test_get_multiple_attr_text_from_xpath(netexdocument):
    path = ["organisations", "Operator", "PublicCode"]
    actual = netexdocument.get_multiple_attr_text_from_xpath(path)
    expected = ["HCTY", "ATOC", "NR"]
    assert expected == actual


def test_get_multiple_attr_ids_from_xpath(netexdocument):
    path = ["lines", "Line"]
    actual = netexdocument.get_multiple_attr_ids_from_xpath(path)
    expected = ["16"]
    assert expected == actual


def test_get_atco_area_code(netexdocument):
    actual = netexdocument.get_atco_area_code()
    expected = [
        "329",
        "329",
        "329",
        "329",
        "329",
        "329",
        "329",
        "329",
        "329",
        "329",
        "329",
        "329",
        "329",
        "329",
        "329",
    ]
    assert expected == actual


def test_get_valid_from_date(netexdocument):
    actual = netexdocument.get_valid_from_date()
    expected = "2020-01-01"
    assert expected == actual


def test_get_composite_frame_ids(netexdocument):
    actual = netexdocument.get_composite_frame_ids()
    expected = [
        "epd:UK:HCTY:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_16:op",
        "fxc:UK:DFT:TypeOfFrame_UK_PI_METADATA_OFFER:FXCP:fxc",
    ]
    assert expected == actual


def test_get_to_date_texts(netexdocument):
    actual = netexdocument.get_to_date_texts()
    expected = [
        datetime.datetime(2022, 12, 31, 12, 0),
        datetime.datetime(2020, 12, 31, 12, 0),
    ]
    assert expected == actual


def test_get_fare_products(netexdocument):
    actual = netexdocument.fare_products
    assert len(actual) == 1
    assert actual[0].localname == "PreassignedFareProduct"


def test_no_attribute(netexdocument):
    with pytest.raises(AttributeError) as exc_info:
        netexdocument.attr_doesnt_exist()

    expected = "'NeTExDocument' has no attribute 'attr_doesnt_exist'"
    assert str(exc_info.value) == expected


def test_get_earliest_tariff_from_date(netexdocument):
    actual = netexdocument.get_earliest_tariff_from_date()
    expected = parse_datetime_str("2020-06-22T13:51:43.044Z")
    assert expected == actual


def test_get_latest_tariff_to_date(netexdocument):
    actual = netexdocument.get_latest_tariff_to_date()
    expected = parse_datetime_str("2119-06-22T13:51:43.044Z")
    assert expected == actual


def test_get_scheduled_stop_points(netexdocument):
    actual = netexdocument.scheduled_stop_points
    expected = 15
    assert expected == len(actual)
    assert "atco:3290YYA00077" == actual[0]["id"]
    assert "Kingsthorpe" == actual[0].get_element("Name").text


def test_get_scheduled_stop_points_ids(netexdocument):
    actual = netexdocument.get_scheduled_stop_point_ids()
    expected = 15
    assert expected == len(actual)
    assert "atco:3290YYA00077" == actual[0]
    assert "atco:3290YYA00922" == actual[-1]


def test_get_scheduled_stop_point_ref_ids(netexdocument):
    actual = netexdocument.get_scheduled_stop_point_ref_ids()
    assert "atco:3290YYA00077" == actual[0]
    assert "atco:3290YYA00922" == actual[-1]


def test_get_topographic_place_ref_locality_ids(netexdocument):
    actual = netexdocument.get_topographic_place_ref_locality_ids()
    expected = 15
    assert expected == len(actual)
    assert "E0043573" == actual[0]
    assert "E0055251" == actual[-1]
