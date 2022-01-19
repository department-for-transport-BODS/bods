from typing import Optional

from pydantic import BaseModel
from pyproj import CRS, Transformer

BNG = CRS("EPSG:27700")
WGS84 = CRS("EPSG:4326")
transformer = Transformer.from_crs(BNG, WGS84)


class Translation(BaseModel):
    grid_type: Optional[str]
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
        easting = xml.findtext("./x:Easting", namespaces=ns)
        northing = xml.findtext("./x:Northing", namespaces=ns)
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
    grid_type: Optional[str]
    easting: Optional[int]
    northing: Optional[int]
    translation: Translation

    @classmethod
    def from_xml(cls, location):
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
    short_common_name: Optional[str]
    street: Optional[str]
    indicator: Optional[str]

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


class StopPoint(BaseModel):
    atco_code: str
    naptan_code: Optional[str]
    administrative_area_ref: str
    descriptor: Descriptor
    place: Place

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
        )
