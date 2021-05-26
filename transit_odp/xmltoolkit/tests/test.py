import os

from django.core.files import File
from django.test import TestCase

from transit_odp.xmltoolkit.xml_toolkit import XmlToolkit, XmlToolkitResultStatus


class XmlToolkitTestCase(TestCase):
    def setUp(self):
        self.cur_dir = os.path.abspath(os.path.dirname(__file__))
        namespaces = {}
        self.xml_toolkit = XmlToolkit(namespaces=namespaces)
        self.file = File(os.path.join(self.cur_dir, "data/simple.xml"))

    # Tests for valid xml
    def test_parse_xml_file(self):
        # test
        doc, result = self.xml_toolkit.parse_xml_file(self.file)

        # assert
        self.assertIsNotNone(doc)
        self.assertEqual(result.status, XmlToolkitResultStatus.success)

    # Tests can select multiple elements
    def test_get_elements(self):
        # setup
        doc, result = self.xml_toolkit.parse_xml_file(self.file)

        # test
        authors = self.xml_toolkit.get_elements(doc, "/root/authors/author")

        # assert
        self.assertEqual(3, len(authors))
        self.assertEqual("author", authors[0].tag)
        self.assertEqual("author", authors[1].tag)
        self.assertEqual("author", authors[2].tag)

    # Tests can select non-existent elements
    def test_get_non_existent_elements(self):
        # setup
        doc, result = self.xml_toolkit.parse_xml_file(self.file)

        # test
        authors = self.xml_toolkit.get_elements(doc, "/root/authors/missing")

        # assert
        self.assertEqual(0, len(authors))

    # Tests can select a single expected element
    def test_get_element(self):
        # setup
        doc, result = self.xml_toolkit.parse_xml_file(self.file)

        # test
        country = self.xml_toolkit.get_element(doc, "/root/countries/country")

        # assert
        self.assertEqual("country", country.tag)

    # Tests select a missing expected element throws
    def test_get_element_throws(self):
        # setup
        doc, result = self.xml_toolkit.parse_xml_file(self.file)

        # test
        with self.assertRaises(Exception):
            self.xml_toolkit.get_element(doc, "/root/missing")

    # Tests can select a single optional element
    def test_get_optional_element(self):
        # setup
        doc, result = self.xml_toolkit.parse_xml_file(self.file)

        # test
        country = self.xml_toolkit.get_optional_element(doc, "/root/countries/country")

        # assert
        self.assertEqual("country", country.tag)

    # Tests can select a single optional element when it is missing
    def test_get_optional_element_missing(self):
        # setup
        doc, result = self.xml_toolkit.parse_xml_file(self.file)

        # test
        self.assertIsNone(self.xml_toolkit.get_optional_element(doc, "/root/missing"))

    # Tests can select text of a single element
    def test_get_text(self):
        # setup
        doc, result = self.xml_toolkit.parse_xml_file(self.file)

        # test
        country = self.xml_toolkit.get_text(doc, "/root/countries/country")

        # assert
        self.assertEqual("UK", country)

    # Tests can select text of an optional single element
    def test_get_optional_text(self):
        # setup
        doc, result = self.xml_toolkit.parse_xml_file(self.file)

        # test
        country = self.xml_toolkit.get_optional_text(doc, "/root/countries/country")

        # assert
        self.assertEqual("UK", country)

    # Tests can select text of an optional single element
    def test_get_optional_text_missing(self):
        # setup
        doc, result = self.xml_toolkit.parse_xml_file(self.file)

        # test
        text = self.xml_toolkit.get_optional_text(doc, "/root/missing")

        # assert
        self.assertIsNone(text)

    # Tests can select attribute of a single element
    def test_get_attribute(self):
        # setup
        doc, result = self.xml_toolkit.parse_xml_file(self.file)
        country = self.xml_toolkit.get_element(doc, "/root/countries/country")

        # test
        id = self.xml_toolkit.get_attribute(country, "id")

        # assert
        self.assertEqual("6", id)
