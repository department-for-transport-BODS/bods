from typing import List, Tuple, Union

from lxml import etree

from .exceptions import (
    NoElement,
    ParentDoesNotExist,
    TooManyElements,
    XMLAttributeError,
)


class XMLElement:
    """A class that makes dealing with lxml Element objects easier.

    Args:
        element: lxml.etree.Element you want to traverse.

    """

    namespaces = None

    def __init__(self, element):
        self._element = element

    def __eq__(self, other):
        return self._element == other._element

    def __repr__(self):
        attribs = [f"{key}={value!r}" for key, value in self._element.items()]
        if self.text is None:
            text = "None"
        else:
            text = self.text

        attribs.append(f"text={text.strip()!r}")
        attrib_str = ", ".join(attribs)
        return f"{self.localname}({attrib_str})"

    def __getitem__(self, item):
        try:
            return self._element.attrib[item]
        except KeyError as exc:
            msg = f"{self.localname!r} has no attribute {item!r}"
            raise XMLAttributeError(msg) from exc

    def get(self, item, default=None):
        try:
            return self[item]
        except XMLAttributeError:
            return default

    def get_elements(self, xpath: Union[str, List[str], Tuple[str]]):
        """Gets elements matching xpath.

        Args:
            xpath: Either list/tuple of strings or a regular xpath string.

        Returns:
            A list of elements.

        Raises:
            NoElement: if xpath returns no elements.
        """
        elements = self.xpath(xpath)
        if len(elements) == 0:
            msg = f"{self.localname} has no xpath {xpath!r}"
            raise NoElement(msg)
        return elements

    def get_element(self, xpath: Union[str, List[str], Tuple[str]]):
        """Gets element matching xpath.

        Args:
            xpath: Either list/tuple of strings or a regular xpath string.

        Returns:
            A single element.

        Raises:
            TooManyElements: if xpath returns more than 1 element.
            NoElement: if xpath returns no elements.
        """
        elements = self.get_elements(xpath)

        if len(elements) > 1:
            msg = "More than 1 element found"
            raise TooManyElements(msg)

        return elements[0]

    def get_first_element(self, xpath: Union[str, List[str], Tuple[str]]):
        elements = self.get_elements(xpath)
        return elements[0]

    def get_element_or_none(self, xpath: Union[str, List[str], Tuple[str]]):
        try:
            return self.get_element(xpath)
        except NoElement:
            return None

    def get_elements_or_none(self, xpath: Union[str, List[str], Tuple[str]]):
        try:
            return self.get_elements(xpath)
        except NoElement:
            return None

    def get_first_text_or_default(
        self, xpath: Union[str, List[str], Tuple[str]], default: str = ""
    ):
        try:
            element = self.get_first_element(xpath)
        except NoElement:
            return default

        text = element.text
        if text is None:
            return default

        return text

    def get_text_or_default(
        self, xpath: Union[str, List[str], Tuple[str]], default: str = ""
    ) -> str:
        element = self.get_element_or_none(xpath)
        if element is None:
            return default
        if element.text is None:
            return default
        return element.text

    def _make_xpath(self, xpath) -> str:
        if isinstance(xpath, (list, tuple)):
            xpath = "/".join(xpath)
        return xpath

    def _apply_xpath(self, xpath):
        elements = self._element.xpath(xpath, namespaces=self.namespaces)
        return [self.__class__(element) for element in elements]

    def find_anywhere(self, xpath: Union[str, List[str], Tuple[str]]):
        """Attempts to find a matching xpath anywhere in the tree."""
        xpath = self._make_xpath(xpath)
        xpath = ".//" + xpath
        return self._apply_xpath(xpath)

    def xpath(self, xpath: Union[str, List[str], Tuple[str]]):
        """Wrapper method around Element.xpath allowing for list tags.

        Allows for xpath to specified as list ["Tag1", "Tag2"], this gets
        converted to "Tag1/Tag2"

        Args:
            xpath: Either list/tuple of strings or a regular xpath string.

        Returns:
            elements: A list XMLElements that match the xpath.

        """
        xpath = self._make_xpath(xpath)
        return self._apply_xpath(xpath)

    @property
    def localname(self):
        """Returns the localised tag name with namespaces removed."""
        localname = etree.QName(self._element.tag).localname
        return localname

    @property
    def text(self):
        """Returns the text property of the current root element."""
        return self._element.text

    @property
    def children(self):
        """Returns the children elements of the current root element."""
        return [self.__class__(element) for element in self._element.getchildren()]

    @property
    def parent(self):
        """Returns the parent of the element."""
        element = self._element.getparent()
        if element is None:
            msg = f"{self.localname!r} has no parent element"
            raise ParentDoesNotExist(msg)

        return self.__class__(element)

    @property
    def line_number(self):
        """Returns the line number of the element."""
        return self._element.sourceline

    @property
    def tag_localname(self):
        """Returns the local name (tag without namespace) of the current element."""
        return etree.QName(self._element).localname
