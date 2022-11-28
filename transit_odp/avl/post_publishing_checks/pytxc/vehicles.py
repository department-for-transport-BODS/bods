from datetime import time
from typing import List, Optional

from .elements import Element
from .journeys import JourneyPatternRef, JourneyPatternTimingLinkRef
from .operators import OperatorRef
from .services import LineRef, OperatingProfile, ServiceRef


class Block(Element):
    @property
    def description(self) -> Optional[str]:
        return self.find_text("Description")

    @property
    def block_number(self) -> Optional[str]:
        return self.find_text("BlockNumber")


class TicketMachine(Element):
    @property
    def journey_code(self) -> Optional[str]:
        path = "JourneyCode"
        return self.find_text(path)


class Operational(Element):
    @property
    def block(self):
        path = "Block"
        element = self.find(path)
        if element is not None:
            return Block(element)
        return None

    @property
    def ticket_machine(self):
        path = "TicketMachine"
        element = self.find(path)
        if element is not None:
            return TicketMachine(element)
        return None


class VehicleJourneyTimingLink(Element):
    @property
    def run_time(self) -> Optional[str]:
        path = "RunTime"
        return self.find_text(path)

    @property
    def journey_pattern_timing_link_ref(self) -> Optional[JourneyPatternTimingLinkRef]:
        path = "JourneyPatternTimingLinkRef"
        return self._create_ref(path, JourneyPatternTimingLinkRef)


class VehicleJourney(Element):
    @property
    def private_code(self) -> Optional[str]:
        path = "PrivateCode"
        return self.find_text(path)

    @property
    def direction(self) -> Optional[str]:
        path = "Direction"
        return self.find_text(path)

    @property
    def operational(self) -> Optional[Operational]:
        path = "Operational"
        element = self.find(path)
        if element is not None:
            return Operational(element)
        return None

    @property
    def vehicle_journey_code(self) -> Optional[str]:
        path = "VehicleJourneyCode"
        return self.find_text(path)

    @property
    def service_ref(self) -> Optional[ServiceRef]:
        path = "ServiceRef"
        return self._create_ref(path, ServiceRef)

    @property
    def line_ref(self) -> Optional[LineRef]:
        path = "LineRef"
        return self._create_ref(path, LineRef)

    @property
    def operator_ref(self) -> Optional[OperatorRef]:
        path = "OperatorRef"
        return self._create_ref(path, OperatorRef)

    @property
    def journey_pattern_ref(self) -> Optional[JourneyPatternRef]:
        path = "JourneyPatternRef"
        return self._create_ref(path, JourneyPatternRef)

    @property
    def departure_time(self) -> Optional[time]:
        path = "DepartureTime"
        departure = self.find_text(path)
        if departure is not None:
            return time.fromisoformat(departure)
        return None

    @property
    def timing_links(self) -> List[VehicleJourneyTimingLink]:
        path = "VehicleJourneyTimingLink"
        return [VehicleJourneyTimingLink(element) for element in self.find_all(path)]

    @property
    def operating_profile(self) -> Optional[OperatingProfile]:
        path = "OperatingProfile"
        element = self.find(path)
        if element is not None:
            return OperatingProfile(element)
        return None
