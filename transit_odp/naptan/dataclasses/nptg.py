from typing import List

from pydantic import BaseModel


class Descriptor(BaseModel):
    locality_name: str

    @classmethod
    def from_xml(cls, xml):
        ns = {"x": xml.nsmap.get(None)}
        return cls(
            locality_name=xml.findtext("./x:LocalityName", namespaces=ns),
        )


class Translation(BaseModel):
    easting: int
    northing: int
    longitude: float
    latitude: float

    @classmethod
    def from_xml(cls, xml):
        ns = {"x": xml.nsmap.get(None)}
        return cls(
            easting=xml.findtext("./x:Easting", namespaces=ns),
            northing=xml.findtext("./x:Northing", namespaces=ns),
            longitude=xml.findtext("./x:Longitude", namespaces=ns).strip(),
            latitude=xml.findtext("./x:Latitude", namespaces=ns).strip(),
        )


class Location(BaseModel):
    translation: Translation

    @classmethod
    def from_xml(cls, xml):
        ns = {"x": xml.nsmap.get(None)}
        return cls(
            translation=Translation.from_xml(
                xml.find("./x:Translation", namespaces=ns)
            ),
        )


class NptgLocality(BaseModel):
    nptg_locality_code: str
    descriptor: Descriptor
    administrative_area_ref: str
    nptg_district_ref: str
    source_locality_type: str
    location: Location

    @classmethod
    def from_xml(cls, xml):
        ns = {"x": xml.nsmap.get(None)}
        return cls(
            nptg_locality_code=xml.findtext("./x:NptgLocalityCode", namespaces=ns),
            descriptor=Descriptor.from_xml(xml.find("./x:Descriptor", namespaces=ns)),
            administrative_area_ref=xml.findtext(
                "./x:AdministrativeAreaRef", namespaces=ns
            ),
            nptg_district_ref=xml.findtext("./x:NptgDistrictRef", namespaces=ns),
            source_locality_type=xml.findtext("./x:SourceLocalityType", namespaces=ns),
            location=Location.from_xml(xml.find("./x:Location", namespaces=ns)),
        )


class AdministrativeArea(BaseModel):
    administrative_area_code: str
    atco_area_code: str
    name: str
    short_name: str
    national: int

    @classmethod
    def from_xml(cls, xml):
        ns = {"x": xml.nsmap.get(None)}
        return cls(
            administrative_area_code=xml.findtext(
                "./x:AdministrativeAreaCode", namespaces=ns
            ),
            atco_area_code=xml.findtext("./x:AtcoAreaCode", namespaces=ns),
            name=xml.findtext("./x:Name", namespaces=ns),
            short_name=xml.findtext("./x:ShortName", namespaces=ns),
            national=xml.findtext("./x:National", namespaces=ns),
        )


class Region(BaseModel):
    region_code: str
    name: str
    country: str
    administrative_areas: List[AdministrativeArea]

    @classmethod
    def from_xml(cls, xml):
        ns = {"x": xml.nsmap.get(None)}
        region_code = xml.findtext("./x:RegionCode", namespaces=ns)
        name = xml.findtext("./x:Name", namespaces=ns)
        country = xml.findtext("./x:Country", namespaces=ns)
        admin_areas = xml.iterfind(
            "./x:AdministrativeAreas/x:AdministrativeArea", namespaces=ns
        )
        return cls(
            region_code=region_code,
            name=name,
            country=country,
            administrative_areas=(
                AdministrativeArea.from_xml(area) for area in admin_areas
            ),
        )


class NationalPublicTransportGazetteer(BaseModel):
    regions: List[Region]
    nptg_localities: List[NptgLocality]

    @classmethod
    def from_xml(cls, xml):
        ns = {"x": xml.nsmap.get(None)}
        regions = xml.iterfind("./x:Regions/x:Region", namespaces=ns)
        localities = xml.iterfind("./x:NptgLocalities/x:NptgLocality", namespaces=ns)
        return cls(
            regions=(Region.from_xml(region) for region in regions),
            nptg_localities=(
                NptgLocality.from_xml(locality) for locality in localities
            ),
        )
