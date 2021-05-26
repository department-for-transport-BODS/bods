from enum import Enum
from typing import BinaryIO, Tuple

import attr
from lxml import etree
from lxml.etree import ElementTree, XMLSchema


class XmlToolkitResultStatus(Enum):
    success = 1
    invalid_file = 2
    invalid_xml = 3
    unknown_error = 4
    schema_validation_failed = 5


@attr.s
class XmlToolkitResult(object):
    status: XmlToolkitResultStatus
    message: str


def parse_xml_file(source: BinaryIO) -> Tuple[ElementTree, XmlToolkitResult]:
    """
    Checks that the file is valid xml.
    Returns an lxml::ElementTree.
    """

    doc = None
    try:
        doc = etree.parse(source)
        result = XmlToolkitResult()
        result.status = XmlToolkitResultStatus.success
        return doc, result

    # check for filepath IO error
    except IOError:
        result = XmlToolkitResult()
        result.status = XmlToolkitResultStatus.invalid_file
        return doc, result

    # check for XML syntax errors
    except etree.XMLSyntaxError as err:
        result = XmlToolkitResult()
        result.status = XmlToolkitResultStatus.invalid_xml
        result.message = str(err.error_log)
        return doc, result

    except Exception:
        result = XmlToolkitResult()
        result.status = XmlToolkitResultStatus.unknown_error
        result.message = "Unknown exception"
        return doc, result


class XmlToolkit(object):
    def __init__(self, namespaces):
        self.namespaces = namespaces

    def parse_xml_file(self, source: BinaryIO) -> Tuple[ElementTree, XmlToolkitResult]:
        return parse_xml_file(source)

    def get_schema(self, schema_url: str) -> XMLSchema:
        xmlschema_doc = etree.parse(schema_url)
        return etree.XMLSchema(xmlschema_doc)

    # Validates an xml doc against a schema
    def validate(
        self, doc: ElementTree, xmlschema: XMLSchema
    ) -> XmlToolkitResultStatus:
        try:
            xmlschema.assertValid(doc)
            result = XmlToolkitResult()
            result.status = XmlToolkitResultStatus.success
            return result

        except etree.DocumentInvalid as err:
            result = XmlToolkitResult()
            result.status = XmlToolkitResultStatus.schema_validation_failed
            result.message = str(err.error_log)
            return result

        except Exception:
            result = XmlToolkitResult()
            result.status = XmlToolkitResultStatus.schema_validation_failed
            result.message = "Unknown exception"
            return result

    def get_element(self, root, xpath):
        """
        Search root for the given xpath, resolving to a single element.
        Return the element.
        Throws if a single element is not found.
        """
        elements = root.xpath(xpath, namespaces=self.namespaces)
        if len(elements) != 1:
            raise Exception(f"Expected 1 element {xpath}. Got {len(elements)}")
        else:
            return elements[0]

    def get_child(self, root, child_tag):
        """
        Search root for the given child, resolving to a single element.
        Return the element.
        """
        # TODO SJB what happens if child not found?
        return root.find(child_tag, namespaces=self.namespaces)

    # Search root for the given xpath
    def get_elements(self, root, xpath):
        elements = root.xpath(xpath, namespaces=self.namespaces)
        return elements

    def get_optional_element(self, root, xpath):
        """
        Search root for the given xpath, resolving to a single element.
        Return the element or None.
        """
        elements = root.xpath(xpath, namespaces=self.namespaces)
        if len(elements) != 1:
            return None
        else:
            return elements[0]

    def get_text(self, root, xpath) -> str:
        """
        Search root for the given xpath, resolving to a single element.
        Return the text of that element.
        Throws if a single element is not found.
        """
        elements = root.xpath(xpath, namespaces=self.namespaces)
        if len(elements) != 1:
            raise Exception(f"Expected 1 element {xpath}. Got {len(elements)}")
        else:
            return elements[0].text

    def get_child_text(self, root, child_tag) -> str:
        """
        Search root for the given child, resolving to a single element.
        Return the text of that element.
        Returns None if child doesn't exist.
        """
        return root.findtext(child_tag, namespaces=self.namespaces)

    def get_optional_text(self, root, xpath):
        """
        Search root for the given xpath, resolving to zero or one element.
        Return the text of that element, or None
        """
        elements = root.xpath(xpath, namespaces=self.namespaces)
        if len(elements) != 1:
            return None
        else:
            return elements[0].text

    def get_attribute(self, root, attr):
        return root.get(attr)
