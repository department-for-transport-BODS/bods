from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import IO, AnyStr, List, Optional

from lxml import etree

from .elements import Element
from .journeys import JourneyPatternSection
from .operators import Operator
from .routes import Route, RouteSection
from .services import Service
from .stops import AnnotatedStopPointRef
from .vehicles import VehicleJourney


@dataclass
class Header:
    creation_date_time: Optional[datetime]
    modification_date_time: Optional[datetime]
    file_name: str
    modification: str
    schema_version: str
    revision_number: Optional[int]


class Timetable(Element):
    def __repr__(self) -> str:
        return (
            f"Timetable(file_name={self.header.file_name!r}, "
            f"revision_number={self.header.revision_number})"
        )

    def _get_datetime_attr(self, key: str) -> Optional[datetime]:
        date_time = self.attributes.get(key)
        if date_time is not None:
            return datetime.fromisoformat(date_time)
        return None

    @property
    def header(self):
        revision_number_str = self.attributes.get("RevisionNumber")
        if revision_number_str is not None:
            revision_number = int(revision_number_str)
        else:
            revision_number = None

        return Header(
            creation_date_time=self._get_datetime_attr("CreationDateTime"),
            modification_date_time=self._get_datetime_attr("ModificationDateTime"),
            file_name=self.attributes.get("FileName", ""),
            modification=self.attributes.get("Modification", ""),
            schema_version=self.attributes.get("SchemaVersion", ""),
            revision_number=revision_number,
        )

    @property
    def operators(self) -> List[Operator]:
        path = "Operators/Operator"
        return [Operator(element) for element in self.find_all(path)]

    @property
    def services(self) -> List[Service]:
        path = "Services/Service"
        return [Service(element) for element in self.find_all(path)]

    @property
    def stop_points(self) -> List[AnnotatedStopPointRef]:
        path = "StopPoints/AnnotatedStopPointRef"
        return [AnnotatedStopPointRef(element) for element in self.find_all(path)]

    @property
    def route_sections(self):
        path = "RouteSections/RouteSection"
        return [RouteSection(element) for element in self.find_all(path)]

    @property
    def routes(self):
        path = "Routes/Route"
        return [Route(element) for element in self.find_all(path)]

    @property
    def journey_pattern_sections(self):
        path = "JourneyPatternSections/JourneyPatternSection"
        return [JourneyPatternSection(element) for element in self.find_all(path)]

    @property
    def vehicle_journeys(self):
        path = "VehicleJourneys/VehicleJourney"
        return [VehicleJourney(element) for element in self.find_all(path)]

    @classmethod
    def from_file_path(cls, path: Path) -> "Timetable":
        with path.open("r") as f:
            return cls.from_file(f)

    @classmethod
    def from_file(cls, file: IO[AnyStr]) -> "Timetable":
        element = etree.parse(file).getroot()
        return cls(element)

    @classmethod
    def from_string(cls, xml: str) -> "Timetable":
        element = etree.fromstring(xml)
        return cls(element)
