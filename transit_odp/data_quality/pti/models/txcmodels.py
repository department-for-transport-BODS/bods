from pydantic.main import BaseModel


class VehicleJourney(BaseModel):
    code: str
    line_ref: str
    journey_pattern_ref: str
    vehicle_journey_ref: str

    @classmethod
    def from_xml(cls, xml):
        namespaces = {"x": xml.nsmap.get(None)}
        code = xml.xpath("string(x:VehicleJourneyCode)", namespaces=namespaces)
        line_ref = xml.xpath("string(x:LineRef)", namespaces=namespaces)
        journey_pattern_ref = xml.xpath(
            "string(x:JourneyPatternRef)", namespaces=namespaces
        )
        vehicle_journey_ref = xml.xpath(
            "string(x:VehicleJourneyRef)", namespaces=namespaces
        )
        return cls(
            code=code,
            line_ref=line_ref,
            journey_pattern_ref=journey_pattern_ref,
            vehicle_journey_ref=vehicle_journey_ref,
        )


class Line(BaseModel):
    ref: str
    line_name: str

    @classmethod
    def from_xml(cls, xml):
        namespaces = {"x": xml.nsmap.get(None)}
        ref = xml.xpath("string(@id)", namespaces=namespaces)
        line_name = xml.xpath("string(x:LineName)", namespaces=namespaces)
        return cls(ref=ref, line_name=line_name)
