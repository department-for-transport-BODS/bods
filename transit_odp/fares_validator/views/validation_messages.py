"""
This is to manage all the custom error messages from the validator functions
"""

MESSAGE_OBSERVATION_FARE_PRODUCTS_MISSING = (
    "fareProducts element is missing from FareFrame - UK_PI_FARE_PRODUCT"
)

MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT = (
    "Mandatory element 'FareStructureElement' missing"
)
MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT_REF = (
    "Mandatory element 'FareStructureElement.TypeOfFareStructureElementRef' missing"
)
MESSAGE_OBSERVATION_GENERIC_PARAMETER = (
    "Mandatory element 'FareStructureElement.GenericParameterAssignment' missing"
)
MESSAGE_OBSERVATION_ACCESS_RIGHT_ASSIGNMENT = (
    "Mandatory element 'GenericParameterAssignment."
    "TypeOfAccessRightAssignmentRef' missing"
)
MESSAGE_OBSERVATION_FARE_STRUCTURE_COMBINATIONS = (
    "'FareStructureElement' checks failed: Present at least 3 times,"
    "check the 'ref' values are in the correct combination for both "
    "'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements."
)
