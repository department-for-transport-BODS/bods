from typing import Optional

from .elements import Element, Ref


class StopPointRef(Ref):
    def resolve(self) -> None:
        pass


class AnnotatedStopPointRef(Element):
    def __repr__(self) -> str:
        return (
            f"AnnotatedStopPointRef(stop_point_ref={self.stop_point_ref!r}, "
            f"common_name={self.common_name!r})"
        )

    @property
    def stop_point_ref(self) -> Optional[StopPointRef]:
        path = "StopPointRef"
        element = self.find(path)
        if element is not None:
            return StopPointRef(element)

        return None

    @property
    def common_name(self) -> Optional[str]:
        return self.find_text("CommonName")
