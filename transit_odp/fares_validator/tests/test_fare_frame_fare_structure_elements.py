import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    all_fare_structure_element_checks,
)

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}


def get_lxml_element(string_xml):
    doc = etree.fromstring(string_xml)
    xpath = "//x:fareStructureElements"
    service_frames = doc.xpath(xpath, namespaces=NAMESPACE)
    return service_frames


@pytest.mark.parametrize(
    (
        "type_of_fare_str_element_ref_attr_present",
        "type_of_access_right_assig_ref_attr_present",
        "access_fare_structure_absent",
        "eligibility_fare_structure_absent",
        "travel_condition_fare_structure_absent",
        "length_fare_structure_elements_greater_than_two",
        "ref_values_combination_correct",
        "expected",
    ),
    [
        (True, True, False, False, False, True, True, None),
        (
            False,
            True,
            True,
            False,
            False,
            True,
            False,
            [
                "violation",
                "5",
                "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
            ],
        ),
        (
            True,
            False,
            False,
            False,
            True,
            True,
            False,
            [
                "violation",
                "5",
                "Attribute 'ref' of element 'TypeOfAccessRightAssignmentRef' is missing",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            False,
            True,
            True,
            [
                "violation",
                "5",
                "'FareStructureElement' checks failed: Present at least 3 times, check the 'ref' values are in the correct combination for both 'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements.",
            ],
        ),
        (
            True,
            True,
            False,
            True,
            False,
            True,
            True,
            [
                "violation",
                "5",
                "'FareStructureElement' checks failed: Present at least 3 times, check the 'ref' values are in the correct combination for both 'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements.",
            ],
        ),
        (
            True,
            True,
            False,
            False,
            True,
            True,
            True,
            [
                "violation",
                "5",
                "'FareStructureElement' checks failed: Present at least 3 times, check the 'ref' values are in the correct combination for both 'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements.",
            ],
        ),
        (
            True,
            True,
            False,
            False,
            False,
            False,
            True,
            [
                "violation",
                "5",
                "'FareStructureElement' checks failed: Present at least 3 times, check the 'ref' values are in the correct combination for both 'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements.",
            ],
        ),
        (
            True,
            True,
            False,
            False,
            False,
            True,
            False,
            [
                "violation",
                "5",
                "'FareStructureElement' checks failed: Present at least 3 times, check the 'ref' values are in the correct combination for both 'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements.",
            ],
        ),
    ],
)
def test_all_fare_structure_element_checks(
    type_of_fare_str_element_ref_attr_present,
    type_of_access_right_assig_ref_attr_present,
    access_fare_structure_absent,
    eligibility_fare_structure_absent,
    travel_condition_fare_structure_absent,
    length_fare_structure_elements_greater_than_two,
    ref_values_combination_correct,
    expected,
):
    fare_str_with_children = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    type_of_fare_str_element_attr_missing = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    type_of_access_right_assignment_attr_missing = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0"/>
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_str_access_missing = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_str_eligibility_missing = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_str_travel_conditions_missing = """
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_str_less_than_three = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_str_incorrect_combination = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            {0}
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    if type_of_fare_str_element_ref_attr_present:
        if type_of_access_right_assig_ref_attr_present:
            if not access_fare_structure_absent:
                if not eligibility_fare_structure_absent:
                    if not travel_condition_fare_structure_absent:
                        if length_fare_structure_elements_greater_than_two:
                            if ref_values_combination_correct:
                                xml = fare_frames.format(fare_str_with_children)
                            else:
                                xml = fare_frames.format(fare_str_incorrect_combination)
                        else:
                            xml = fare_frames.format(fare_str_less_than_three)
                    else:
                        xml = fare_frames.format(fare_str_travel_conditions_missing)
                else:
                    xml = fare_frames.format(fare_str_eligibility_missing)
            else:
                xml = fare_frames.format(fare_str_access_missing)
        else:
            xml = fare_frames.format(type_of_access_right_assignment_attr_missing)
    else:
        xml = fare_frames.format(type_of_fare_str_element_attr_missing)

    fare_structure_elements = get_lxml_element(xml)
    result = all_fare_structure_element_checks("", fare_structure_elements)
    assert result == expected
