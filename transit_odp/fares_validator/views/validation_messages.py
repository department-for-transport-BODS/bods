"""
This is to manage all the custom error messages from the validator functions
"""
MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING = (
    "TypeOfFrameRef 'ref' attribute is missing from FareFrame"
)
MESSAGE_OBSERVATION_FARE_STRCUTURE_REF_MISSING = (
    "TypeOfFareStructureElementRef 'ref' attribute is missing from FareStructureElement"
)
MESSAGE_OBSERVATION_FARE_PRODUCTS_MISSING = (
    "fareProducts element is missing from FareFrame - UK_PI_FARE_PRODUCT"
)
MESSAGE_OBSERVATION_TARIFF_REF_MISSING = "TypeOfTariffRef is missing"
MESSAGE_OBSERVATION_INCORRECT_TARIFF_REF = "TypeOfTariffRef has unexpected value"
MESSAGE_OBSERVATION_FARE_TABLES_MISSING = (
    "fareTables missing from FareFrame - UK_PI_FARE_PRICE"
)
MESSAGE_OBSERVATION_FARE_TABLE_MISSING = (
    "FareTable missing from fareTables in FareFrame- UK_PI_FARE_PRICE"
)
MESSAGE_OBSERVATION_PRICES_FOR_MISSING = (
    "PricesFor missing from FareTable in FareFrame- UK_PI_FARE_PRICE"
)
MESSAGE_OBSERVATION_PREASSIGNED_FARE_MISSING = (
    "PreassignedFareProduct missing in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
)
MESSAGE_OBSERVATION_PREASSIGNED_FARE_NAME_MISSING = "Name missing from PreassignedFareProduct in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PREASSIGNED_TYPE_OF_FARE_MISSING = "TypeOfFareProductRef missing from PreassignedFareProduct in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PREASSIGNED_FARE_CHARGING_MISSING = "ChargingMomentType missing from PreassignedFareProduct in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_ELEMENTS_MISSING = "validableElements missing from PreassignedFareProduct in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_ELEMENT_MISSING = "ValidableElement missing from PreassignedFareProduct in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_FARE_MISSING = "fareStructureElements missing from PreassignedFareProduct in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_FARE_REF_MISSING = "FareStructureElementRef missing from PreassignedFareProduct in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PREASSIGNED_ACCESS_MISSING = "accessRightsInProduct missing from PreassignedFareProduct in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PREASSIGNED_ACCESS_VALIDABLE_MISSING = "ValidableElementRef missing from PreassignedFareProduct/accessRightsInProduct in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_PREASSIGNED_PRODUCT_TYPE_MISSING = "ProductType missing from PreassignedFareProduct in fareProducts for FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_PACKAGES_MISSING = (
    "salesOfferPackages element is missing from FareFrame - UK_PI_FARE_PRODUCT"
)
MESSAGE_OBSERVATION_SALES_OFFER_PACKAGE_MISSING = "salesOfferPackage element is missing from salesOfferPackages in FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_ASSIGNMENTS_MISSING = "distributionAssignments element is missing from SalesOfferPackage in FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_ASSIGNMENT_MISSING = "DistributionAssignment element is missing from SalesOfferPackage/distributionAssignments in FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_DIST_CHANNEL_TYPE_MISSING = "DistributionChannelType element is missing from SalesOfferPackage/distributionAssignments in FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_PAYMENT_METHODS_MISSING = "PaymentMethods element is missing from SalesOfferPackage/distributionAssignments in FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_ELEMENTS_MISSING = "salesOfferPackageElements element is missing from SalesOfferPackage in FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_ELEMENT_MISSING = "SalesOfferPackageElement element is missing from SalesOfferPackage/salesOfferPackageElements in FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_TRAVEL_DOC_MISSING = "TypeOfTravelDocumentRef element is missing from SalesOfferPackage/salesOfferPackageElements/SalesOfferPackageElement in FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_SALES_OFFER_FARE_PROD_REF_MISSING = "PreassignedFareProductRef element is missing from SalesOfferPackage/salesOfferPackageElements/SalesOfferPackageElement in FareFrame - UK_PI_FARE_PRODUCT"
MESSAGE_OBSERVATION_GENERIC_PARAMETER_ACCESS_PROPS_MISSING = "ValidityParameterGroupingType or ValidityParameterAssignmentType and validityParameters elements are missing from GenericParameterAssignment when 'TypeOfFareStructureElementRef' has a ref value of 'fxc:access'"
MESSAGE_OBSERVATION_GENERIC_PARAMETER_ELIGIBILITY_PROPS_MISSING = "UserProfile and it's child elements 'Name' and 'UserType' are missing from GenericParameterAssignment when 'TypeOfFareStructureElementRef' has a ref value of 'fxc:eligibility'"
MESSAGE_OBSERVATION_GENERIC_PARAMETER_FREQUENCY_MISSING = "FrequencyOfUse is missing from GenericParameterAssignment when 'TypeOfFareStructureElementRef' has a ref value of 'fxc:travel_conditions'"
MESSAGE_OBSERVATION_GENERIC_PARAMETER_FREQUENCY_TYPE_MISSING = "FrequencyOfUseType is missing from GenericParameterAssignment/limitations/FrequencyOfUse when 'TypeOfFareStructureElementRef' has a ref value of 'fxc:travel_conditions'"
