from abc import abstractmethod
from typing import Dict, List, Optional, Type, TypeVar, Union

from lxml.etree import _Element

R = TypeVar("R", bound="Ref")


class Element:
    def __init__(self, element: Union["Element", _Element]):

        if isinstance(element, _Element):
            self._element = element
        else:
            self._element = element._element
        self.nsmap = {None: "http://www.transxchange.org.uk/"}

    def __repr__(self):
        class_name = self.__class__.__name__
        attrs = []
        if self.text:
            attrs.append(f"text={self.text!r}")
        attrs += [f"{key}={value!r}" for key, value in self.attributes.items()]
        attrs_str = ", ".join(attrs)
        return f"{class_name}({attrs_str})"

    @property
    def id(self) -> str:
        return self.attributes.get("id", "")

    @property
    def text(self) -> Optional[str]:
        text = self._element.text
        if text is not None:
            return text.strip()
        return None

    @property
    def attributes(self) -> Dict[str, str]:
        return {str(key): str(value) for key, value in self._element.attrib.items()}

    def _create_ref(self, path: str, element_class: Type[R]) -> Optional[R]:
        element = self.find(path)
        if element is not None:
            return element_class(element)
        return None

    def find(self, path: str) -> Optional["Element"]:
        kwargs = {"namespaces": self.nsmap}
        element = self._element.find(path, **kwargs)  # type: ignore
        if element is not None:
            return Element(element)
        return None

    def find_all(self, path: str) -> List["Element"]:
        kwargs = {"namespaces": self.nsmap}
        return [
            Element(element)
            for element in self._element.findall(path, **kwargs)  # type: ignore
        ]

    def find_text(self, path: str) -> Optional[str]:
        kwargs = {"namespaces": self.nsmap}
        return self._element.findtext(path, **kwargs)  # type: ignore

    def get_parent(self) -> Optional["Element"]:
        parent = self._element.getparent()
        if parent is not None:
            return Element(parent)
        return None

    def get_children(self) -> List["Element"]:
        return [Element(element) for element in self._element.iterchildren()]

    def get_root(self) -> "Element":
        return Element(self._element.getroottree().getroot())

    @property
    def line_number(self) -> Optional[int]:
        return self._element.sourceline  # type: ignore


E = TypeVar("E", bound=Element)


class Ref:
    path: str = ""

    def __init__(self, ref: Element):
        self.ref = ref

    @property
    def text(self):
        return self.ref.text

    @property
    def root(self):
        return self.ref.get_root()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(text={self.text})"

    def _resolve(self, element_class: Type[E]) -> E:
        path = self.path + f"[@id='{self.text}']"
        element = self.root.find(path)
        if element is None:
            raise NotImplementedError()
        return element_class(element)

    @abstractmethod
    def resolve(self):
        pass
