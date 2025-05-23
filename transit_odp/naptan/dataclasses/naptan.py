from typing import List, Optional

from pydantic import BaseModel, field_validator
from pyproj import CRS, Transformer

BNG = CRS("EPSG:27700")
WGS84 = CRS("EPSG:4326")
transformer = Transformer.from_crs(BNG, WGS84)


class Translation(BaseModel):
    grid_type: Optional[str] = None
    easting: int
    northing: int
    longitude: float
    latitude: float

    @classmethod
    def from_xml(cls, xml):
        """
        Create a Translation object from lxml naptan:Translation.
        """
        ns = {"x": xml.nsmap.get(None)}
        easting = xml.findtext("./x:Easting", namespaces=ns).strip()
        northing = xml.findtext("./x:Northing", namespaces=ns).strip()
        latitude, longitude = transformer.transform(float(easting), float(northing))
        return cls(
            grid_type=xml.findtext("./x:GridType", namespaces=ns),
            easting=easting,
            northing=northing,
            longitude=longitude,
            latitude=latitude,
        )

    @classmethod
    def from_bng(cls, easting: float, northing: float, grid_type: str):
        """
        Create a Translation object from easting and northing.
        """
        latitude, longitude = transformer.transform(easting, northing)
        return cls(
            grid_type=grid_type,
            longitude=longitude,
            latitude=latitude,
            easting=easting,
            northing=northing,
        )


class Location(BaseModel):
    grid_type: Optional[str] = None
    easting: Optional[int] = None
    northing: Optional[int] = None
    translation: Translation
    sequence_number: Optional[int] = None

    @field_validator("easting", mode="before")
    def parse_easting(cls, v):
        if not v:
            return v

        if isinstance(v, str):
            v = v.strip()
        return int(v)

    @field_validator("northing", mode="before")
    def parse_northing(cls, v):
        if not v:
            return v

        if isinstance(v, str):
            v = v.strip()
        return int(v)

    @classmethod
    def from_xml(cls, location, sequence_number=None):
        """
        Create a Location from an lxml naptan:Location.
        """
        ns = {"x": location.nsmap.get(None)}
        grid_type = location.findtext("./x:GridType", namespaces=ns)
        easting = location.findtext("./x:Easting", namespaces=ns)
        northing = location.findtext("./x:Northing", namespaces=ns)

        translation = location.find("./x:Translation", namespaces=ns)
        if translation is not None:
            translation = Translation.from_xml(translation)
        else:
            translation = Translation.from_bng(
                float(easting), float(northing), grid_type
            )
        return cls(
            easting=easting,
            northing=northing,
            grid_type=grid_type,
            translation=translation,
            sequence_number=sequence_number,
        )


class Place(BaseModel):
    nptg_locality_ref: str
    location: Location

    @classmethod
    def from_xml(cls, xml):
        """
        Create a Place from an lxml naptan:Place.
        """
        ns = {"x": xml.nsmap.get(None)}
        return cls(
            nptg_locality_ref=xml.findtext("./x:NptgLocalityRef", namespaces=ns),
            location=Location.from_xml(xml.find("./x:Location", namespaces=ns)),
        )


class Descriptor(BaseModel):
    common_name: str
    short_common_name: Optional[str] = None
    street: Optional[str] = None
    indicator: Optional[str] = None

    @classmethod
    def from_xml(cls, xml):
        """
        Create a Descriptor from an lxml naptan:Descriptor.
        """
        ns = {"x": xml.nsmap.get(None)}
        common_name = xml.findtext("./x:CommonName", namespaces=ns)
        short_common_name = xml.findtext("./x:ShortCommonName", namespaces=ns)
        street = xml.findtext("./x:Street", namespaces=ns)
        indicator = xml.findtext("./x:Indicator", namespaces=ns)
        return cls(
            common_name=common_name,
            short_common_name=short_common_name,
            street=street,
            indicator=indicator,
        )


class FlexibleZone(BaseModel):
    location: Optional[list[Location]]

    @classmethod
    def from_xml(cls, xml):
        """
        Create a Translation object from lxml naptan:Translation.
        """
        ns = {"x": xml.nsmap.get(None)}
        locations_xml = xml.findall(".//x:Location", namespaces=ns)
        location = []
        if locations_xml is not None:
            location = [
                Location.from_xml(element, index + 1)
                for index, element in enumerate(locations_xml)
            ]
        return cls(location=location)


class Bus(BaseModel):
    bus_stop_type: str
    flexible_zones: Optional[FlexibleZone]

    @classmethod
    def from_xml(cls, xml):
        """
        Create a Translation object from lxml naptan:Translation.
        """
        ns = {"x": xml.nsmap.get(None)}
        bus_stop_type = xml.findtext("./x:BusStopType", namespaces=ns)
        flexible_zone_xml = xml.find("./x:FlexibleZone", namespaces=ns)
        flexible_zones = None
        if flexible_zone_xml is not None:
            flexible_zones = FlexibleZone.from_xml(flexible_zone_xml)
        return cls(bus_stop_type=bus_stop_type, flexible_zones=flexible_zones)


class OnStreet(BaseModel):
    bus: Optional[Bus] = None

    @classmethod
    def from_xml(cls, xml):
        """
        Create a Translation object from lxml naptan:Translation.
        """
        ns = {"x": xml.nsmap.get(None)}
        bus_xml = xml.find("./x:Bus", namespaces=ns)
        bus = None
        if bus_xml is not None:
            bus = Bus.from_xml(bus_xml)
        return cls(bus=bus)


class StopClassification(BaseModel):
    stop_type: Optional[str] = None
    on_street: Optional[OnStreet] = None

    @classmethod
    def from_xml(cls, xml):
        """
        Create a Translation object from lxml naptan:Translation.
        """
        ns = {"x": xml.nsmap.get(None)}
        stop_type = xml.findtext("./x:StopType", namespaces=ns)
        on_street_xml = xml.find("./x:OnStreet", namespaces=ns)
        on_street = None
        if on_street_xml is not None:
            on_street = OnStreet.from_xml(on_street_xml)
        return cls(stop_type=stop_type, on_street=on_street)


class StopPoint(BaseModel):
    atco_code: str
    naptan_code: Optional[str] = None
    administrative_area_ref: str
    descriptor: Descriptor
    place: Place
    stop_areas: List[str]
    stop_classification: StopClassification

    @classmethod
    def from_xml(cls, xml):
        """
        Create a StopPoint from an lxml naptan:StopPoint.
        """
        ns = {"x": xml.nsmap.get(None)}
        return cls(
            atco_code=xml.findtext("./x:AtcoCode", namespaces=ns),
            naptan_code=xml.findtext("./x:NaptanCode", namespaces=ns),
            administrative_area_ref=xml.findtext(
                "./x:AdministrativeAreaRef", namespaces=ns
            ),
            descriptor=Descriptor.from_xml(xml.find("./x:Descriptor", namespaces=ns)),
            place=Place.from_xml(xml.find("./x:Place", namespaces=ns)),
            stop_areas=[
                element.text
                for element in xml.findall(".//x:StopAreaRef", namespaces=ns)
            ],
            stop_classification=StopClassification.from_xml(
                xml.find("./x:StopClassification", namespaces=ns)
            ),
        )
