"""
This is to manage all the custom error messages from the validator functions
"""

MESSAGE_OBSERVATION_FARE_PRODUCTS_MISSING = (
    "fareProducts element is missing from FareFrame - UK_PI_FARE_PRODUCT"
)

MESSAGE_OBSERVATION_TYPE_OF_FARE_FRAME_REF_MISSING = (
    "Attribute 'ref' of element 'TypeOfFrameRef' is missing or "
    "attribute 'ref' value does not contain "
    "'UK_PI_FARE_PRODUCT' or 'UK_PI_FARE_PRICE'"
)
MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_ID_MISSING = (
    "From 'scheduledStopPoints' element in ServiceFrame, "
    "attribute 'id' of element 'ScheduledStopPoint' is missing"
)
MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_NAME_MISSING = (
    "From 'scheduledStopPoints' element in ServiceFrame, " "element 'Name' is missing"
)
MESSAGE_OBSERVATION_SCHEDULED_STOP_POINTS_MISSING = (
    "Element 'scheduledStopPoints' is missing"
)
MESSAGE_OBSERVATION_NAME_MISSING = (
    "From 'Line' element in ServiceFrame, " "element 'Name' is missing"
)
MESSAGE_OBSERVATION_PUBLICCODE_MISSING = (
    "From 'Line' element in ServiceFrame, " "element 'PublicCode' is missing"
)
MESSAGE_OBSERVATION_OPERATORREF_MISSING = (
    "From 'Line' element in ServiceFrame, " "element'OperatorRef' is missing"
)
MESSAGE_OBSERVATION_LINES_MISSING = "Element 'lines' is missing in ServiceFrame"
MESSAGE_OBSERVATION_SERVICEFRAME_TYPE_OF_FRAME_REF_MISSING = (
    "If 'ServiceFrame' is present, TypeOfFrameRef should include UK_PI_NETWORK"
)
MESSAGE_OBSERVATION_PUBLIC_CODE_LENGTH = (
    "Element 'Public Code' should be 4 characters long"
)
MESSAGE_OBSERVATION_OPERATOR_ID = "'Operator' attribute 'id' format should be noc:xxxx"
MESSAGE_OBSERVATION_COMPOSITE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING = (
    "Attribute 'ref' value does not contain "
    "'UK_PI_LINE_FARE_OFFER' or 'UK_PI_NETWORK_OFFER'"
)
MESSAGE_OBSERVATION_FARE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING = (
    "Attribute 'ref' value does not contain 'UK_PI_FARE_NETWORK'"
)
MESSAGE_OBSERVATION_FARE_ZONE_MISSING = (
    "Element 'FareZone' is missing within 'fareZones'"
)
MESSAGE_OBSERVATION_FARE_ZONES_NAME_MISSING = (
    "Element 'Name' is missing within the element 'FareZone'"
)
MESSAGE_OBSERVATION_FARE_ZONES_MEMBERS_MISSING = (
    "Element 'members' is missing within the element 'FareZone'"
)
MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_REF_MISSING = (
    "Element 'ScheduledStopPointRef' is missing within the element 'members'"
)
MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_TEXT_MISSING = (
    "Value missing within element 'ScheduledStopPointRef'"
)
MESSAGE_OBSERVATION_ROUND_TRIP_MISSING = (
    "Element 'RoundTrip' is missing within 'limitations'"
)
MESSAGE_OBSERVATION_TRIP_TYPE_MISSING = (
    "Element 'TripType' is missing within 'RoundTrip'"
)
MESSAGE_OBSERVATION_TIME_INTERVALS_MISSING = (
    "Element 'timeIntervals' is missing within 'FareStructureElement'"
)
MESSAGE_OBSERVATION_TIME_INTERVAL_REF_MISSING = (
    "Element 'TimeIntervalRef' is missing within 'timeIntervals'"
)
MESSAGE_OBSERVATION_TARIFF_TIME_INTERVALS_MISSING = (
    "Element 'timeIntervals' is missing within 'Tariff'"
)
MESSAGE_OBSERVATION_TARIFF_TIME_INTERVAL_MISSING = (
    "Element 'TimeInterval' is missing within 'timeIntervals'"
)
MESSAGE_OBSERVATION_TARIFF_NAME_MISSING = (
    "Element 'Name' is missing within 'TimeInterval'"
)
MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT = (
    "Mandatory element 'FareStructureElement' is missing"
)
MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT_REF = (
    "Mandatory element 'FareStructureElement.TypeOfFareStructureElementRef' is missing"
)
MESSAGE_OBSERVATION_GENERIC_PARAMETER = (
    "Mandatory element 'FareStructureElement.GenericParameterAssignment' is missing"
)
MESSAGE_OBSERVATION_ACCESS_RIGHT_ASSIGNMENT = (
    "Mandatory element 'GenericParameterAssignment."
    "TypeOfAccessRightAssignmentRef' is missing"
)
MESSAGE_OBSERVATION_FARE_STRUCTURE_COMBINATIONS = (
    "'FareStructureElement' checks failed: Present at least 3 times, "
    "check the 'ref' values are in the correct combination for both "
    "'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements."
)
MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING = (
    "Attribute 'ref' of element 'FareStructureElement' is missing"
)
MESSAGE_GENERIC_PARA_ASSIGNEMENT_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING = (
    "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing"
)
MESSAGE_TYPE_OF_FRAME_REF_MISSING = (
    "Attribute 'ref' of element 'TypeOfFrameRef' is missing"
)
MESSAGE_OPERATORS_ID_MISSING = "'Operator' attribute 'id' is missing"
