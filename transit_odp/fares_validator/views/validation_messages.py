"""
This is to manage all the custom error messages from the validator functions
"""
MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING = (
    "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'"
)
MESSAGE_OBSERVATION_FARE_PRODUCTS_MISSING = "'fareProducts' and it's child elements is missing from 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_TARIFF_REF_MISSING = (
    "Mandatory element 'TypeOfTariffRef' is missing in 'Tariff'"
)
MESSAGE_OBSERVATION_TYPE_OF_TARIFF_REF_MISSING = (
    "'TypeOfTariffRef' 'ref' attribute is missing in 'Tariff'"
)
MESSAGE_OBSERVATION_TARIFF_OPERATOR_REF_MISSING = (
    "Mandatory element 'OperatorRef' or 'GroupOfOperatorsRef' missing in 'Tariff'"
)
MESSAGE_OBSERVATION_TARIFF_TARIFF_BASIS_MISSING = (
    "Mandatory element 'TariffBasis' is missing in 'Tariff'"
)
MESSAGE_OBSERVATION_TARIFF_VALIDITY_CONDITIONS_MISSING = (
    "Mandatory element 'validityConditions' is missing in 'Tariff'"
)
MESSAGE_OBSERVATION_TARIFF_VALID_BETWEEN_MISSING = (
    "Mandatory element 'ValidBetween' is missing in 'Tariff.validityConditions'"
)
MESSAGE_OBSERVATION_TARIFF_FROM_DATE_MISSING = "Mandatory element 'FromDate' is missing or empty in 'Tariff.validityConditions.ValidBetween'"
MESSAGE_OBSERVATION_INCORRECT_TARIFF_REF = "'TypeOfTariffRef' has unexpected value"
MESSAGE_OBSERVATION_FARE_TABLES_MISSING = (
    "'fareTables' missing from 'FareFrame' - UK_PI_FARE_PRICE"
)
MESSAGE_OBSERVATION_FARE_TABLE_MISSING = (
    "'FareTable' missing from 'fareTables' in 'FareFrame'- UK_PI_FARE_PRICE"
)
MESSAGE_OBSERVATION_PRICES_FOR_MISSING = (
    "'PricesFor' missing from 'FareTable' in 'FareFrame'- UK_PI_FARE_PRICE"
)
MESSAGE_OBSERVATION_FARE_MISSING = "'{}' and it's child elements in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PRODUCT_FARE_NAME_MISSING = (
    "'Name' missing from '{}' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
)
MESSAGE_OBSERVATION_TYPE_OF_FARE_MISSING = "'TypeOfFareProductRef' missing from '{}' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_FARE_CHARGING_MISSING = "'ChargingMomentType' missing from '{}' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_FARE_VALIDABLE_ELEMENTS_MISSING = "'validableElements' and it's child elements missing from '{}' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_FARE_VALIDABLE_ELEMENT_MISSING = "'ValidableElement' missing from '{}' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_FARE_VALIDABLE_FARE_MISSING = "'fareStructureElements' and it's child elements missing from '{}' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_FARE_VALIDABLE_FARE_REF_MISSING = "'FareStructureElementRef' missing from '{}' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_ACCESS_MISSING = "'accessRightsInProduct' missing from '{}' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_ACCESS_VALIDABLE_MISSING = "'ValidableElementRef' missing from 'accessRightsInProduct' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PRODUCT_TYPE_MISSING = "'ProductType' missing or empty from '{}' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_WRONG_PRODUCT_TYPE = "'ProductType' for 'AmountOfPriceUnitProduct' in 'fareProducts' must be tripCarnet or passCarnet"
MESSAGE_OBSERVATION_SALES_OFFER_PACKAGES_MISSING = "'salesOfferPackages' and it's child elements is missing from 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_PACKAGE_MISSING = "'salesOfferPackage' and it's child elements is missing from 'salesOfferPackages' in 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_ASSIGNMENTS_MISSING = "'distributionAssignments' and it's child elements is missing from 'salesOfferPackage' in 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_ASSIGNMENT_MISSING = "'DistributionAssignment' and it's child elements is missing from 'distributionAssignments' in 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_DIST_CHANNEL_TYPE_MISSING = "'DistributionChannelType' element is missing or empty from 'DistributionAssignment' in 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_PAYMENT_METHODS_MISSING = "'PaymentMethods' element is missing or empty from 'DistributionAssignment' in 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_ELEMENTS_MISSING = "'salesOfferPackageElements' and it's child elements is missing from 'salesOfferPackage' in 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_ELEMENT_MISSING = "'SalesOfferPackageElement' and it's child elements is missing from 'salesOfferPackageElements' in 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_TRAVEL_DOC_MISSING = "'TypeOfTravelDocumentRef' element is missing from 'SalesOfferPackageElement' in 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_FARE_PROD_REF_MISSING = "'PreassignedFareProductRef' and 'AmountOfPriceUnitProductRef' element is missing from 'SalesOfferPackageElement' in 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_VALIDITY_GROUPING_PARAMETER = "'ValidityParameterGroupingType' or 'ValidityParameterAssignmentType' elements are missing from 'GenericParameterAssignment' when 'TypeOfFareStructureElementRef' has a ref value of 'fxc:access'"
MESSAGE_OBSERVATION_VALIDITY_PARAMETER = "'validityParameters' elements are missing from 'GenericParameterAssignment' when 'TypeOfFareStructureElementRef' has a ref value of 'fxc:access'"
MESSAGE_OBSERVATION_GENERIC_PARAMETER_LIMITATIONS_USER = "Mandatory element 'UserProfile' is missing from 'GenericParameterAssignment' when 'TypeOfFareStructureElementRef' has a 'ref' value of 'fxc:eligibility'"
MESSAGE_OBSERVATION_GENERIC_PARAMETER_ELIGIBILITY_PROPS_MISSING = "Mandatory element 'UserProfile.Name' or 'UserProfile.UserType' is missing from 'GenericParameterAssignment' when 'TypeOfFareStructureElementRef' has a 'ref' value of 'fxc:eligibility'"
MESSAGE_OBSERVATION_GENERIC_PARAMETER_FREQUENCY_MISSING = "'FrequencyOfUse' is missing from 'GenericParameterAssignment' when 'TypeOfFareStructureElementRef' has a 'ref' value of 'fxc:travel_conditions'"
MESSAGE_OBSERVATION_GENERIC_PARAMETER_FREQUENCY_TYPE_MISSING = "'FrequencyOfUseType' is missing or empty from 'GenericParameterAssignment.limitations.FrequencyOfUse' when 'TypeOfFareStructureElementRef' has a 'ref' value of 'fxc:travel_conditions'"
MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_ELEMENT_MISSING = (
    "Mandatory element 'TypeOfFrameRef' is missing from 'FareFrame' - UK_PI_FARE_PRICE"
)
MESSAGE_OBSERVATION_TYPE_OF_FARE_FRAME_REF_INCORRECT = (
    "Attribute 'ref' of element 'TypeOfFrameRef' does not include 'UK_PI_FARE_PRICE'"
)
MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_ELEMENT_FARE_PRODUCT_MISSING = "Mandatory element 'TypeOfFrameRef' is missing from 'FareFrame' - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_TYPE_OF_FARE_FRAME_REF_FARE_PRODUCT_INCORRECT = (
    "Attribute 'ref' of element 'TypeOfFrameRef' does not include 'UK_PI_FARE_PRODUCT'"
)
MESSAGE_OBSERVATION_RESOURCE_FRAME_TYPE_OF_FRAME_REF_ELEMENT_MISSING = (
    "Mandatory element 'TypeOfFrameRef' is missing from 'ResourceFrame' - UK_PI_COMMON"
)
MESSAGE_OBSERVATION_RESOURCE_FRAME_TYPE_OF_FARE_FRAME_REF_INCORRECT = (
    "Attribute 'ref' of element 'TypeOfFrameRef' does not include 'UK_PI_COMMON'"
)
MESSAGE_OBSERVATION_TYPE_OF_FARE_FRAME_REF_MISSING = "Attribute 'ref' of element 'TypeOfFrameRef' does not contain 'UK_PI_FARE_PRODUCT' or 'UK_PI_FARE_PRICE'"
MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_MISSING = "From 'scheduledStopPoints' element in ServiceFrame, element 'ScheduledStopPoint' is missing"
MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_ID_FORMAT = (
    "Attribute 'id' of element 'ScheduledStopPoint' should be in 'atco:xxxx' format"
)
MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_NAME_MISSING = "From 'scheduledStopPoints' element in ServiceFrame, element 'Name' is missing or empty"
MESSAGE_OBSERVATION_SCHEDULED_STOP_POINTS_MISSING = (
    "Element 'scheduledStopPoints' is missing"
)
MESSAGE_OBSERVATION_LINE_MISSING = "Mandatory element 'Line' in ServiceFrame is missing"
MESSAGE_OBSERVATION_NAME_MISSING = (
    "From 'Line' element in ServiceFrame, element 'Name' is missing or empty"
)
MESSAGE_OBSERVATION_PUBLICCODE_MISSING = (
    "From 'Line' element in ServiceFrame, element 'PublicCode' is missing or empty"
)
MESSAGE_OBSERVATION_OPERATORREF_MISSING = (
    "From 'Line' element in ServiceFrame, element'OperatorRef' is missing"
)
MESSAGE_OBSERVATION_LINES_MISSING = "Element 'lines' is missing in ServiceFrame"
MESSAGE_OBSERVATION_SERVICEFRAME_TYPE_OF_FRAME_REF_MISSING = (
    "If 'ServiceFrame' is present, mandatory element 'TypeOfFrameRef' "
    "should be included and TypeOfFrameRef should include UK_PI_NETWORK"
)
MESSAGE_OBSERVATION_PUBLIC_CODE_LENGTH = (
    "Element 'Public Code' should be 4 characters long"
)
MESSAGE_OBSERVATION_OPERATOR_ID = "'Operator' attribute 'id' format should be noc:xxxx"
MESSAGE_OBSERVATION_COMPOSITE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING = (
    "Attribute 'ref' of 'TypeOfFrameRef' in 'CompositeFrame' does not contain "
    "'UK_PI_LINE_FARE_OFFER' or 'UK_PI_NETWORK_FARE_OFFER'"
)
MESSAGE_OBSERVATION_FARE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING = (
    "Mandatory element 'TypeOfFrameRef' is missing or "
    "'ref' value does not contain 'UK_PI_FARE_NETWORK'"
)
MESSAGE_OBSERVATION_FARE_ZONE_MISSING = (
    "Element 'FareZone' is missing within 'fareZones'"
)
MESSAGE_OBSERVATION_FARE_ZONES_NAME_MISSING = (
    "Element 'Name' is missing or empty within the element 'FareZone'"
)
MESSAGE_OBSERVATION_ROUND_TRIP_MISSING = (
    "Element 'RoundTrip' is missing within ''limitations''"
)
MESSAGE_OBSERVATION_TRIP_TYPE_MISSING = (
    "Element 'TripType' is missing within 'RoundTrip'"
)
MESSAGE_OBSERVATION_TIME_INTERVALS_MISSING = (
    "Element 'timeIntervals' is missing within 'FareStructureElement'"
)
MESSAGE_OBSERVATION_TIME_INTERVAL_REF_MISSING = (
    "Element 'TimeIntervalRef' is missing or empty within 'timeIntervals'"
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
MESSAGE_OBSERVATION_GENERIC_PARAMETER = "Mandatory element 'FareStructureElement.GenericParameterAssignment' and it's child elements is missing"
MESSAGE_OBSERVATION_GENERIC_PARAMETER_LIMITATION = "Mandatory element 'FareStructureElement.GenericParameterAssignment.limitations' is missing"
MESSAGE_OBSERVATION_ACCESS_RIGHT_ASSIGNMENT = (
    "Mandatory element 'GenericParameterAssignment."
    "TypeOfAccessRightAssignmentRef' is missing"
)
MESSAGE_OBSERVATION_FARE_STRUCTURE_COMBINATIONS = (
    "'FareStructureElement' checks failed: Present at least 3 times, "
    "check the 'ref' values are in the correct combination for both "
    "'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements."
)
MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT_REF = (
    "Mandatory element 'TypeOfFareStructureElementRef' is missing"
)
MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING = (
    "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing"
)
MESSAGE_TYPE_OF_FRAME_REF_MISSING = (
    "Attribute 'ref' of element 'TypeOfFrameRef' is missing"
)
MESSAGE_OPERATORS_ID_MISSING = "'Operator' attribute 'id' is missing"
MESSAGE_STOP_POINT_ATTR_ID_MISSING = (
    "Attribute 'id' of element 'ScheduledStopPoint' is missing"
)
MESSAGE_OBSERVATION_COMPOSITE_FRAME_VALID_BETWEEN_MISSING = (
    "Mandatory element 'ValidBetween' within 'CompositeFrame' is missing"
)
MESSAGE_OBSERVATION_COMPOSITE_FRAME_FROM_DATE = "Mandatory element 'FromDate' within 'CompositeFrame.ValidBetween' is missing or empty"
MESSAGE_OBSERVATION_RESOURCE_FRAME_MISSING = (
    "Mandatory element 'ResourceFrame' missing from 'CompositeFrame'"
)
MESSAGE_OBSERVATION_RESOURCE_FRAME_ORG_MISSING = (
    "Mandatory element 'organisations' within 'ResourceFrame' is missing"
)
MESSAGE_OBSERVATION_RESOURCE_FRAME_OPERATOR_MISSING = (
    "Mandatory element 'Operator' within 'ResourceFrame.organisations' is missing"
)
MESSAGE_OBSERVATION_RESOURCE_FRAME_PUBLIC_CODE_MISSING = "Mandatory element 'PublicCode' within 'ResourceFrame.organisations.Operator' is missing"
MESSAGE_OBSERVATION_RESOURCE_FRAME_OPERATOR_NAME_MISSING = "Mandatory element 'Name' within 'ResourceFrame.organisations.Operator' is missing or empty"

MESSAGE_TYPE_OF_ACCESS_RIGHT_REF_MISSING = (
    "Attribute 'ref' of element 'TypeOfAccessRightAssignmentRef' is missing"
)
MESSAGE_OBSERVATION_COMPOSITE_FRAME_ID_MISSING = (
    "Attribute 'id' of element 'CompositeFrame' is missing"
)
MESSAGE_OBSERVATION_MISSING_MULTI_OPERATOR_REFS = "At least two 'OperatorRef' should be present in 'ResourceFrame.groupsOfOperators.GroupOfOperators.members'"
MESSAGE_OBSERVATION_MISSING_CAPPED_DISCOUNT_RIGHT_ID = (
    "Attribute 'id' of element 'CappedDiscountRight' is missing"
)
MESSAGE_OBSERVATION_MISSING_CAPPING_RULE_NAME = (
    "Mandatory element 'Name' within 'cappingRules.CappingRule' is missing"
)
MESSAGE_OBSERVATION_MISSING_CAPPING_PERIOD = (
    "Mandatory element 'CappingPeriod' within 'cappingRules.CappingRule' is missing"
)
MESSAGE_OBSERVATION_MISSING_VALIDABLE_ELEMENT_REF = "Mandatory element 'ValidableElementRef' within 'cappingRules.CappingRule' is missing"
