from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from .elements import Element, Ref
from .journeys import JourneyPattern


class Line(Element):
    def __repr__(self) -> str:
        return f"Line(id={self.id!r}, line_name={self.line_name!r})"

    @property
    def line_name(self) -> Optional[str]:
        path = "LineName"
        return self.find_text(path)


class LineRef(Ref):
    path = "Services/Service/Lines/Line"

    def resolve(self) -> Line:
        return super()._resolve(Line)


class OperatingPeriod(Element):
    def __repr__(self) -> str:
        return (
            f"OperatingPeriod(start_date={self.start_date!r}, "
            f"end_date={self.end_date!r})"
        )

    @property
    def start_date(self) -> Optional[date]:
        path = "StartDate"
        date_str = self.find_text(path)
        if date_str is not None:
            return datetime.fromisoformat(date_str).date()

        return None

    @property
    def end_date(self) -> Optional[date]:
        path = "EndDate"
        date_str = self.find_text(path)
        if date_str is not None:
            return datetime.fromisoformat(date_str).date()

        return None


class DayOfWeek(Enum):
    monday = "Monday"
    tuesday = "Tuesday"
    wednesday = "Wednesday"
    thursday = "Thursday"
    friday = "Friday"
    saturday = "Saturday"
    sunday = "Sunday"

    @classmethod
    def from_weekday_int(cls, weekday: int) -> "DayOfWeek":
        """Create DayOfWeek object from zero-based integer, compatible with
        library method date.weekday()
        """
        map = {
            0: cls.monday,
            1: cls.tuesday,
            2: cls.wednesday,
            3: cls.thursday,
            4: cls.friday,
            5: cls.saturday,
            6: cls.sunday,
        }
        return map[weekday]


class OperatingProfile(Element):
    def __repr__(self) -> str:
        if self.holidays_only:
            return "OperatingProfile(holidays only)"
        days_of_week = self.days_of_week
        if len(days_of_week) == 0:
            return "OperatingProfile(none)"
        return f"OperatingProfile({' '.join([d.value for d in days_of_week])})"

    @property
    def holidays_only(self) -> bool:
        path = "RegularDayType/HolidaysOnly"
        elem = self.find(path)
        return elem is not None

    @property
    def days_of_week(self) -> List[DayOfWeek]:
        path = "RegularDayType/DaysOfWeek"
        days_of_week_elem = self.find(path)
        applicable_days = []
        if days_of_week_elem is not None:
            for day in DayOfWeek:
                if days_of_week_elem.find(day.value) is not None:
                    applicable_days.append(day)
        return applicable_days


class StandardService(Element):
    def __repr__(self) -> str:
        return (
            f"StandardService(origin={self.origin!r}, "
            f"destination={self.destination!r})"
        )

    @property
    def origin(self) -> Optional[str]:
        path = "Origin"
        return self.find_text(path)

    @property
    def destination(self) -> Optional[str]:
        path = "Destination"
        return self.find_text(path)

    @property
    def use_all_stop_points(self) -> Optional[bool]:
        path = "UseAllStopPoints"
        result = self.find_text(path)
        if result is not None:
            return result == "true"

        return None

    @property
    def journey_patterns(self) -> List[JourneyPattern]:
        path = "JourneyPattern"
        return [JourneyPattern(element) for element in self.find_all(path)]


class Service(Element):
    def __repr__(self) -> str:
        return f"Service(service_code={self.service_code!r})"

    @property
    def service_code(self) -> Optional[str]:
        path = "ServiceCode"
        return self.find_text(path)

    @property
    def lines(self) -> List[Line]:
        path = "Lines/Line"
        return [Line(element) for element in self.find_all(path)]

    @property
    def operating_period(self) -> Optional[OperatingPeriod]:
        path = "OperatingPeriod"
        element = self.find(path)
        if element is not None:
            return OperatingPeriod(element)
        return None

    @property
    def operating_profile(self) -> Optional[OperatingProfile]:
        path = "OperatingProfile"
        element = self.find(path)
        if element is not None:
            return OperatingProfile(element)
        return None

    @property
    def standard_services(self) -> List[StandardService]:
        path = "StandardService"
        return [StandardService(element) for element in self.find_all(path)]


class ServiceRef(Ref):
    path = "Services/Service"

    def resolve(self) -> Service:
        return super()._resolve(Service)
