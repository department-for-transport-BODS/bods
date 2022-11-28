from typing import Dict, List, Optional, Tuple, Union

from shapely.geometry import LineString, mapping

from .elements import Element, Ref
from .links import From, To

Coordinates = Tuple[Tuple[float]]
GeoValue = Union[str, Coordinates]


class Location(Element):
    @property
    def longitude(self) -> Optional[float]:
        path = "Longitude"
        value = self.find_text(path)
        if value is not None:
            return float(value)
        return None

    @property
    def latitude(self) -> Optional[float]:
        path = "Latitude"
        value = self.find_text(path)
        if value is not None:
            return float(value)
        return None

    def to_list(self) -> List[float]:
        if self.longitude is not None and self.latitude is not None:
            return [self.longitude, self.latitude]
        return []


class Track(Element):
    @property
    def mapping(self):
        path = "Mapping/Location"
        return [Location(element) for element in self.find_all(path)]

    def to_list(self) -> List[List[float]]:
        return [location.to_list() for location in self.mapping]

    def to_geojson(self) -> Dict[str, GeoValue]:
        line = LineString(self.to_list())
        return mapping(line)


class RouteLink(Element):
    def __repr__(self) -> str:
        return f"RouteLink(id={self.id!r})"

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
    def distance(self) -> Optional[int]:
        path = "Distance"
        distance = self.find_text(path)
        if distance is not None:
            return int(distance)
        return None

    @property
    def track(self) -> Optional[Track]:
        path = "Track"
        element = self.find(path)
        if element is not None:
            return Track(element)
        return None


class RouteLinkRef(Ref):
    path = "RouteSections/RouteSection/RouteLink"

    def resolve(self) -> RouteLink:
        return super()._resolve(RouteLink)


class RouteSection(Element):
    def __repr__(self) -> str:
        return f"RouteSection(id={self.id!r})"

    @property
    def route_links(self) -> List[RouteLink]:
        path = "RouteLink"
        return [RouteLink(element) for element in self.find_all(path)]


class RouteSectionRef(Ref):
    path = "RouteSections/RouteSection"

    def resolve(self) -> RouteSection:
        return super()._resolve(RouteSection)


class Route(Element):
    def __repr__(self) -> str:
        return (
            f"Route(private_code={self.private_code!r}, "
            f"description={self.description!r})"
        )

    @property
    def private_code(self):
        return self.find_text("PrivateCode")

    @property
    def description(self):
        return self.find_text("Description")

    @property
    def route_section_refs(self) -> List[RouteSectionRef]:
        refs = self.find_all("RouteSectionRef")
        return [RouteSectionRef(ref) for ref in refs]


class RouteRef(Ref):
    path = "Routes/Route"

    def resolve(self) -> Route:
        return super()._resolve(Route)
