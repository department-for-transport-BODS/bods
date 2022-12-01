from typing import Optional

from .elements import Element


class Link(Element):
    @property
    def sequence_number(self) -> Optional[int]:
        key = "SequenceNumber"
        value = self.attributes.get(key, None)
        if value is not None:
            return int(value)
        return None

    @property
    def activity(self) -> Optional[str]:
        path = "Activity"
        return self.find_text(path)

    @property
    def dynamic_destination_display(self) -> Optional[str]:
        path = "DynamicDestinationDisplay"
        return self.find_text(path)

    @property
    def stop_point_ref(self) -> Optional[str]:
        path = "StopPointRef"
        return self.find_text(path)

    @property
    def timing_status(self) -> Optional[str]:
        path = "TimingStatus"
        return self.find_text(path)


class From(Link):
    pass


class To(Link):
    pass
