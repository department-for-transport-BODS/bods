from datetime import date, datetime
from typing import List, Optional, Tuple

from lxml import etree
from lxml.etree import _Element
from pydantic import BaseModel

SIRI_NAMESPACE = "http://www.siri.org.uk/siri"
_NSMAP = {"x": SIRI_NAMESPACE}
_UTF8 = "utf-8"


class SiriParsingError(ValueError):
    pass


class FramedVehicleJourneyRef(BaseModel):
    data_frame_ref: date
    dated_vehicle_journey_ref: str

    @classmethod
    def from_lxml_element(cls, element: _Element) -> "FramedVehicleJourneyRef":
        return cls(
            data_frame_ref=element.findtext("x:DataFrameRef", namespaces=_NSMAP),
            dated_vehicle_journey_ref=element.findtext(
                "x:DatedVehicleJourneyRef", namespaces=_NSMAP
            ),
        )


class VehicleLocation(BaseModel):
    longitude: float
    latitude: float

    @classmethod
    def from_lxml_element(cls, element: _Element) -> "VehicleLocation":
        return cls(
            longitude=element.findtext("x:Longitude", namespaces=_NSMAP),
            latitude=element.findtext("x:Latitude", namespaces=_NSMAP),
        )


class VehicleJourney(BaseModel):
    driver_ref: Optional[str] = None

    @classmethod
    def from_lxml_element(cls, element: _Element) -> "VehicleJourney":
        return cls(
            driver_ref=element.findtext("x:DriverRef", namespaces=_NSMAP),
        )


class Extensions(BaseModel):
    vehicle_journey: Optional[VehicleJourney] = None

    @classmethod
    def from_lxml_element(cls, element: _Element) -> "Extensions":
        vehicle_journey = None
        vehicle_journey_element = element.find("x:VehicleJourney", namespaces=_NSMAP)
        if vehicle_journey_element is not None:
            vehicle_journey = VehicleJourney.from_lxml_element(vehicle_journey_element)
        return cls(
            vehicle_journey=vehicle_journey,
        )


class MonitoredVehicleJourney(BaseModel):
    bearing: Optional[float] = None
    block_ref: Optional[str] = None
    block_ref_linenum: Optional[int] = None
    framed_vehicle_journey_ref: Optional[FramedVehicleJourneyRef] = None
    vehicle_journey_ref: Optional[str] = None
    destination_name: Optional[str] = None
    destination_ref: Optional[str] = None
    destination_ref_linenum: Optional[int] = None
    origin_name: Optional[str] = None
    origin_ref: Optional[str] = None
    origin_ref_linenum: Optional[int] = None
    origin_aimed_departure_time: Optional[datetime] = None
    direction_ref: Optional[str] = None
    direction_ref_linenum: Optional[int] = None
    published_line_name: Optional[str] = None
    line_ref: Optional[str] = None
    vehicle_location: Optional[VehicleLocation] = None
    operator_ref: str
    vehicle_ref: str
    extensions: Optional[Extensions] = None

    @staticmethod
    def get_value_and_line_number(
        element: _Element, xpath: str
    ) -> Tuple[Optional[str], Optional[int]]:
        xpath_elem = element.find(xpath, namespaces=_NSMAP)
        if xpath_elem is not None:
            return (xpath_elem.text, xpath_elem.sourceline)
        return (None, None)

    @classmethod
    def from_lxml_element(cls, element: _Element) -> "MonitoredVehicleJourney":
        block_ref, block_ref_linenum = cls.get_value_and_line_number(
            element, "x:BlockRef"
        )
        direction_ref, direction_ref_linenum = cls.get_value_and_line_number(
            element, "x:DirectionRef"
        )
        origin_ref, origin_ref_linenum = cls.get_value_and_line_number(
            element, "x:OriginRef"
        )
        destination_ref, destination_ref_linenum = cls.get_value_and_line_number(
            element, "x:DestinationRef"
        )
        framed_vehicle_journey_ref = None
        fvjr_element = element.find("x:FramedVehicleJourneyRef", namespaces=_NSMAP)
        if fvjr_element is not None:
            framed_vehicle_journey_ref = FramedVehicleJourneyRef.from_lxml_element(
                fvjr_element
            )

        vehicle_location_element = element.find("x:VehicleLocation", namespaces=_NSMAP)
        if vehicle_location_element is None:
            raise SiriParsingError("missing 'VehicleLocation'.")

        extensions = None
        extensions_element = element.find("x:Extensions", namespaces=_NSMAP)
        if extensions_element is not None:
            extensions = Extensions.from_lxml_element(extensions_element)

        return cls(
            bearing=element.findtext("x:Bearing", namespaces=_NSMAP),
            block_ref=block_ref,
            block_ref_linenum=block_ref_linenum,
            line_ref=element.findtext("x:LineRef", namespaces=_NSMAP),
            direction_ref=direction_ref,
            direction_ref_linenum=direction_ref_linenum,
            published_line_name=element.findtext(
                "x:PublishedLineName", namespaces=_NSMAP
            ),
            operator_ref=element.findtext("x:OperatorRef", namespaces=_NSMAP),
            origin_ref=origin_ref,
            origin_ref_linenum=origin_ref_linenum,
            origin_name=element.findtext("x:OriginName", namespaces=_NSMAP),
            destination_ref=destination_ref,
            destination_ref_linenum=destination_ref_linenum,
            destination_name=element.findtext("x:DestinationName", namespaces=_NSMAP),
            origin_aimed_departure_time=element.findtext(
                "x:OriginAimedDepartureTime", namespaces=_NSMAP
            ),
            framed_vehicle_journey_ref=framed_vehicle_journey_ref,
            vehicle_journey_ref=element.findtext(
                "x:VehicleJourneyRef", namespaces=_NSMAP
            ),
            vehicle_ref=element.findtext("x:VehicleRef", namespaces=_NSMAP),
            vehicle_location=VehicleLocation.from_lxml_element(
                vehicle_location_element
            ),
            extensions=extensions,
        )


class VehicleActivity(BaseModel):
    recorded_at_time: datetime
    item_identifier: Optional[str] = None
    valid_until_time: datetime
    monitored_vehicle_journey: MonitoredVehicleJourney

    @classmethod
    def from_lxml_element(cls, element: _Element) -> "VehicleActivity":
        mvj_element = element.find("x:MonitoredVehicleJourney", namespaces=_NSMAP)
        if mvj_element is None:
            raise SiriParsingError("missing 'MonitoredVehicleJourney'.")

        return cls(
            recorded_at_time=element.findtext("x:RecordedAtTime", namespaces=_NSMAP),
            item_identifier=element.findtext("x:ItemIdentifier", namespaces=_NSMAP),
            valid_until_time=element.findtext("x:ValidUntilTime", namespaces=_NSMAP),
            monitored_vehicle_journey=MonitoredVehicleJourney.from_lxml_element(
                mvj_element
            ),
        )


class VehicleMonitoringDelivery(BaseModel):
    request_message_ref: str
    response_timestamp: datetime
    shortest_possible_cycle: str
    valid_until: datetime
    vehicle_activities: List[VehicleActivity]

    @classmethod
    def from_lxml_element(cls, element: _Element) -> "VehicleMonitoringDelivery":
        activites = [
            VehicleActivity.from_lxml_element(element)
            for element in element.findall("x:VehicleActivity", namespaces=_NSMAP)
        ]
        return cls(
            request_message_ref=element.findtext(
                "x:RequestMessageRef", namespaces=_NSMAP
            ),
            response_timestamp=element.findtext(
                "x:ResponseTimestamp", namespaces=_NSMAP
            ),
            shortest_possible_cycle=element.findtext(
                "x:ShortestPossibleCycle", namespaces=_NSMAP
            ),
            valid_until=element.findtext("x:ValidUntil", namespaces=_NSMAP),
            vehicle_activities=activites,
        )


class ServiceDelivery(BaseModel):
    producer_ref: str
    response_timestamp: datetime
    vehicle_monitoring_delivery: VehicleMonitoringDelivery

    @classmethod
    def from_lxml_element(cls, element: _Element) -> "ServiceDelivery":
        producer_ref = element.findtext("x:ProducerRef", namespaces=_NSMAP)
        response_timestamp = element.findtext("x:ResponseTimestamp", namespaces=_NSMAP)

        vmd_element = element.find("x:VehicleMonitoringDelivery", namespaces=_NSMAP)
        if vmd_element is None:
            raise SiriParsingError("missing 'VehicleMonitoringDelivery'.")
        vehicle_monitoring_delivery = VehicleMonitoringDelivery.from_lxml_element(
            element=vmd_element
        )
        return cls(
            producer_ref=producer_ref,
            response_timestamp=response_timestamp,
            vehicle_monitoring_delivery=vehicle_monitoring_delivery,
        )


class Siri(BaseModel):
    version: str
    service_delivery: ServiceDelivery

    @classmethod
    def from_lxml_element(cls, element: _Element) -> "Siri":
        version = element.attrib["version"]
        sd_element = element.find("x:ServiceDelivery", namespaces=_NSMAP)
        if sd_element is None:
            raise SiriParsingError("missing 'ServiceDelivery'.")
        service_delivery = ServiceDelivery.from_lxml_element(element=sd_element)
        return cls(version=version, service_delivery=service_delivery)

    @classmethod
    def from_string(cls, packet: str) -> "Siri":
        return cls.from_lxml_element(etree.fromstring(packet))

    @classmethod
    def from_bytes(cls, packet: bytes) -> "Siri":
        return cls.from_string(packet.decode(_UTF8))
