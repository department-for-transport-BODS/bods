from typing import List, Optional

from .elements import Element, Ref
from .links import From, To
from .operators import OperatorRef
from .routes import RouteLinkRef, RouteRef


class OperatingProfile(Element):
    pass


class JourneyPatternTimingLink(Element):
    @property
    def from_(self) -> Optional[From]:
        path = "From"
        element = self.find(path)
        if element is not None:
            return From(element)
        return None

    @property
    def to(self) -> Optional[To]:
        path = "To"
        element = self.find(path)
        if element is not None:
            return To(element)
        return None

    @property
    def route_link_ref(self) -> Optional[RouteLinkRef]:
        path = "RouteLinkRef"
        return self._create_ref(path, RouteLinkRef)

    @property
    def run_time(self) -> Optional[str]:
        path = "RunTime"
        return self.find_text(path)


class JourneyPatternTimingLinkRef(Ref):
    element_class = JourneyPatternTimingLink
    path = "JourneyPatternSections/JourneyPatternSection/JourneyPatternTimingLink"

    def resolve(self) -> JourneyPatternTimingLink:
        return super()._resolve(JourneyPatternTimingLink)


class JourneyPatternSection(Element):
    @property
    def timing_links(self) -> List[JourneyPatternTimingLink]:
        path = "JourneyPatternTimingLink"
        return [JourneyPatternTimingLink(element) for element in self.find_all(path)]


class JourneyPatternSectionRef(Ref):
    path = "JourneyPatternSections/JourneyPatternSection"

    def resolve(self) -> JourneyPatternSection:
        return super()._resolve(JourneyPatternSection)


class JourneyPattern(Element):
    @property
    def destination_display(self) -> Optional[str]:
        path = "DestinationDisplay"
        return self.find_text(path)

    @property
    def direction(self) -> Optional[str]:
        path = "Direction"
        return self.find_text(path)

    @property
    def route_ref(self) -> Optional[RouteRef]:
        path = "RouteRef"
        return self._create_ref(path, RouteRef)

    @property
    def operator_ref(self) -> Optional[OperatorRef]:
        path = "OperatorRef"
        return self._create_ref(path, OperatorRef)

    @property
    def journey_pattern_section_refs(self) -> List[JourneyPatternSectionRef]:
        path = "JourneyPatternSectionRefs"
        return [JourneyPatternSectionRef(ref) for ref in self.find_all(path)]


class JourneyPatternRef(Ref):
    path = "Services/Service/StandardService/JourneyPattern"

    def resolve(self) -> JourneyPattern:
        return super()._resolve(JourneyPattern)
