from collections import OrderedDict

from transit_odp.common.utils.choice_enum import ChoiceEnum


class SirivmField(ChoiceEnum):
    VERSION = "Version"
    RESPONSE_TIMESTAMP_SD = "ResponseTimestamp (ServiceDelivery)"
    PRODUCER_REF = "ProducerRef"
    RESPONSE_TIMESTAMP_VMD = "ResponseTimestamp (VehicleMonitoringDelivery)"
    REQUEST_MESSAGE_REF = "RequestMessageRef"
    VALID_UNTIL = "ValidUntil"
    SHORTEST_POSSIBLE_CYCLE = "ShortestPossibleCycle"
    RECORDED_AT_TIME = "RecordedAtTime"
    ITEM_IDENTIFIER = "ItemIdentifier"
    VALID_UNTIL_TIME = "ValidUntilTime"
    LINE_REF = "LineRef"
    DIRECTION_REF = "DirectionRef"
    DATA_FRAME_REF = "DataFrameRef"
    DATED_VEHICLE_JOURNEY_REF = "DatedVehicleJourneyRef"
    PUBLISHED_LINE_NAME = "PublishedLineName"
    OPERATOR_REF = "OperatorRef"
    ORIGIN_REF = "OriginRef"
    ORIGIN_NAME = "OriginName"
    DESTINATION_REF = "DestinationRef"
    DESTINATION_NAME = "DestinationName"
    ORIGIN_AIMED_DEPARTURE_TIME = "OriginAimedDepartureTime"
    LONGITUDE = "Longitude"
    LATITUDE = "Latitude"
    BEARING = "Bearing"
    VEHICLE_REF = "VehicleRef"
    BLOCK_REF = "BlockRef"
    DRIVER_REF = "DriverRef"


class MiscFieldPPC(ChoiceEnum):
    BODS_DATA_FEED_NAME = "BODS data feed name"
    BODS_DATA_FEED_ID = "BODS data feed id"
    BODS_DATASET_ID = "BODS dataset id"
    TXC_FILENAME = "TXC filename"
    TXC_FILE_REVISION = "TXC file revision"
    TXC_DEPARTURE_TIME = "TXC DepartureTime"


class ErrorCategory(ChoiceEnum):
    GENERAL = "General"
    BLOCK_REF = "BlockRef"
    DIRECTION_REF = "DirectionRef"
    DESTINATION_REF = "DestinationRef"
    ORIGIN_REF = "OriginRef"
    DESTINATION_NAME = "DestinationName"
    PUBLISHED_LINE_NAME = "PublishedLineName"


SIRIVM_TO_TXC_MAP = OrderedDict(
    [
        (SirivmField.OPERATOR_REF, "NationalOperatorCode"),
        (SirivmField.LINE_REF, "LineName"),
        (SirivmField.DATED_VEHICLE_JOURNEY_REF, "TicketMachine/JourneyCode"),
        (SirivmField.PUBLISHED_LINE_NAME, "LineName"),
        (SirivmField.DESTINATION_REF, "JourneyPatternTimingLink/To/StopPointRef"),
        (SirivmField.ORIGIN_REF, "JourneyPatternTimingLink/from/StopPointRef"),
        (SirivmField.DIRECTION_REF, "Direction"),
        (SirivmField.BLOCK_REF, "BlockNumber"),
    ]
)
