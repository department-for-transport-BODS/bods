PPC_SUMMARY_FIELDS = {
    "SIRI field": (
        "List of SIRI VM fields where there is an equivalent matching field "
        "in the TxC-PTI data and TXC-PTI fields MUST be an absolute match of "
        "text and formatting."
    ),
    "TXC match field": (
        "List of TxC fields where there is an equivalent matching field in "
        "the SIRI VM data and SIRI VM fields MUST be an absolute match of "
        "text and formatting."
    ),
    "Total vehicleActivities analysed": (
        "The total number of vehicle activities collected from a feed and "
        "analysed per report"
    ),
    "Total count of SIRI fields populated": (
        "The total number of SIRI VM fields populated from the "
        "collected vehicle activities"
    ),
    "%populated": (
        "Percentage figure of SIRI VM fields populated from the "
        "collected vehicle activities"
    ),
    "Successful match with TXC": (
        "The total number of SIRI VM fields successfully matched with "
        "equivalent matching timetables fields"
    ),
    "%match": (
        "Percentage figure of SIRI VM fields successfully matched with "
        "equivalent matching timetables fields"
    ),
    "Notes": (
        "This provides additional details or notes to assist publishers and "
        "suppliers to provide most accurate data"
    ),
}


_siri_vm_standard_field = "Siri VM standard field"

SIRI_MSG_ANALYSED_FIELDS = {
    "Version": _siri_vm_standard_field,
    "ResponseTimestamp (ServiceDelivery)": _siri_vm_standard_field,
    "ProducerRef": _siri_vm_standard_field,
    "ResponseTimestamp (VehicleMonitoringDelivery)": _siri_vm_standard_field,
    "RequestMessageRef": _siri_vm_standard_field,
    "ValidUntil": _siri_vm_standard_field,
    "ShortestPossibleCycle": _siri_vm_standard_field,
    "RecordedAtTime": _siri_vm_standard_field,
    "ItemIdentifier": _siri_vm_standard_field,
    "ValidUntilTime": _siri_vm_standard_field,
    "LineRef": _siri_vm_standard_field,
    "DirectionRef": _siri_vm_standard_field,
    "DataFrameRef": _siri_vm_standard_field,
    "DatedVehicleJourneyRef": _siri_vm_standard_field,
    "PublishedLineName": _siri_vm_standard_field,
    "OperatorRef": _siri_vm_standard_field,
    "OriginRef": _siri_vm_standard_field,
    "OriginName": _siri_vm_standard_field,
    "DestinationRef": _siri_vm_standard_field,
    "DestinationName": _siri_vm_standard_field,
    "OriginAimedDepartureTime": _siri_vm_standard_field,
    "Longitude": _siri_vm_standard_field,
    "Latitude": _siri_vm_standard_field,
    "Bearing": _siri_vm_standard_field,
    "VehicleRef": _siri_vm_standard_field,
    "BlockRef": _siri_vm_standard_field,
    "DriverRef": _siri_vm_standard_field,
}


UNCOUNTED_VEHICLE_ACTIVITIES_FIELDS = {
    "SD ResponseTimestamp": "Time individual response element was created",
    "AVL data set name BODS": (
        "The name of the AVL dataset in BODS that contains the record which "
        "could not be analysed"
    ),
    "AVL data set ID BODS": (
        "The ID of the AVL dataset in BODS that contains the record which "
        "could not be analysed"
    ),
    "OperatorRef": (
        "This shall be the operator's National Operator Code (NOC) from the "
        "Traveline NOC database and same as the ID to the corresponding "
        "object in the timetables data."
    ),
    "LineRef": (
        "Name or number by which the LINE is known to the public. This shall "
        "be the same as the corresponding object in the timetables data "
        "provided to BODS."
    ),
    "RecordedAtTime": "Time at which VEHICLE data was recorded.",
    "DatedVehicleJourneyRef in SIRI": (
        "Unique identifier describing vehicle journey that a vehicle is "
        "running. This shall be the same as the corresponding object in the "
        "timetables data and should be a globally unique identifier."
    ),
    "Error note: Reason it could not be analysed against TXC": (
        "A description of the data that could not be successfully matched. "
        "These align with the steps below and the reasons why a record cannot "
        "be successfully analysed. Reason it could not be analysed to TXC"
    ),
}

SHARED_FIELDS_START = {
    "SD ResponseTimestamp": "Time individual response element was created",
    "RecordedAtTime": "Time at which VEHICLE data was recorded.",
    "AVL data set name BODS": (
        "The internal BODS generated data set name given for an AVL data feed."
    ),
    "AVL data set ID BODS": (
        "The internal BODS generated ID of the operator/publisher providing "
        "data on BODS."
    ),
    "DatedVehicleJourneyRef in SIRI": (
        "Unique identifier describing vehicle journey that a vehicle is "
        "running. This must be the same in the TicketMachine/JourneyCode "
        "as the corresponding object in the timetables data"
    ),
    "VehicleRef in SIRI": "A reference to the specific VEHICLE making a journey.",
    "Timetable file name": (
        "The internal BODS generated data set name given for TxC data set."
    ),
    "Timetable data set ID BODS": (
        "The internal BODS generated ID of the operator/publisher providing "
        "data on BODS"
    ),
    "DepartureTime in TXC": (
        "The departure time from the first stop in the journey pattern"
    ),
}

SHARED_FIELDS_END = {
    "SIRI XML line number": (
        "The exact line number of the file provided to BODS. This is "
        "usually generated by the publisher or their supplier for SIRI VM"
    ),
    "TransXChange XML line number": (
        "The exact line number of the file provided to BODS. This is "
        "usually generated by the publisher or their supplier"
    ),
    "Error note": (
        "This provides additional notes in plain English assisting publishers "
        "and suppliers address the errors identified in the report and "
        "provide most accurate data"
    ),
}

DIRECTION_REF_FIELDS = {
    **SHARED_FIELDS_START,
    "DirectionRef in SIRI": (
        "Direction of the journey (for example INBOUND/OUTBOUND). This must be "
        "the same direction as the corresponding object in the timetables data."
    ),
    "Direction from JourneyPattern in TXC": (
        "Direction of the journey as defined in the Journey Pattern. This "
        "must be the same direction as the corresponding object in the "
        "location data."
    ),
    **SHARED_FIELDS_END,
}


DESTINATION_REF_FIELDS = {
    **SHARED_FIELDS_START,
    "DestinationRef in SIRI": (
        "The identifier of the destination of the journey; used to help "
        "identify the vehicle to the public. This shall be a valid ATCOCode "
        "from the NaPTAN database, and same as the ID to the corresponding "
        "object in the timetables data."
    ),
    "StopPointRef in TxC": (
        "Origin ID of the journey as defined in the "
        "JourneyPatternTimingLink/from/StopPointRef. This must be the "
        "same ID as the corresponding object in the location data."
    ),
    **SHARED_FIELDS_END,
}


ORIGIN_REF_FIELDS = {
    **SHARED_FIELDS_START,
    "OriginRef in SIRI": (
        "The identifier of the origin of the journey; used to help "
        "identify the VEHICLE JOURNEY on arrival boards. This shall be a "
        "valid ATCOCode from the NaPTAN database, and same as the ID to "
        "the corresponding object in the timetables data."
    ),
    "StopPointRef in TxC": (
        "Origin ID of the journey as defined in the "
        "JourneyPatternTimingLink/from/StopPointRef. This must be the "
        "same ID as the corresponding object in the location data."
    ),
    **SHARED_FIELDS_END,
}


BLOCK_REF_FIELDS = {
    **SHARED_FIELDS_START,
    "BlockRef in SIRI": (
        "Block that vehicle is running in SIRI VM. If this has also been "
        "provided in the timetables data, the input should be the same ID "
        "as the corresponding object in the timetables data."
    ),
    "BlockNumber in TXC": "Block number that vehicle is running in TxC",
    **SHARED_FIELDS_END,
}
