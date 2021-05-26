import os

import pytest
from django.core.files import File
from django.test import TestCase

from transit_odp.pipelines.pipelines.dataset_etl.feed_parser import FeedParser
from transit_odp.timetables.constants import TXC_21, TXC_24
from transit_odp.timetables.utils import get_transxchange_schema
from transit_odp.xmltoolkit.xml_toolkit import XmlToolkit, XmlToolkitResultStatus

pytestmark = pytest.mark.django_db

# TODO looks like these are really just XmlFileParser and xml_toolkit unit tests.
# Move to separate test fixtures if so.


class FeedParserTestCase(TestCase):
    def setUp(self):
        self.cur_dir = os.path.abspath(os.path.dirname(__file__))
        self.feed_parser = FeedParser(None, None)
        self.xml_toolkit = XmlToolkit({"x": "http://www.transxchange.org.uk/"})
        self.xml_file_parser = self.feed_parser.extractor

    # Tests for valid xml, but no schema involved
    def test_valid_xml(self):
        file_obj = File(os.path.join(self.cur_dir, "data/ea_20-1A-A-y08-1.xml"))
        doc, result = self.xml_toolkit.parse_xml_file(file_obj.file)
        self.assertIsNotNone(doc)
        self.assertEqual(result.status, XmlToolkitResultStatus.success)

    # Tests for invalid xml
    def test_invalid_xml(self):
        file_obj = File(os.path.join(self.cur_dir, "data/bad.xml"))
        doc, result = self.xml_toolkit.parse_xml_file(file_obj.file)
        self.assertIsNone(doc)
        self.assertEqual(result.status, XmlToolkitResultStatus.invalid_xml)

    # Tests for an invalid or non-existent file
    def test_invalid_file(self):
        file_obj = File(os.path.join(self.cur_dir, "data/invalid.xml"))
        doc, result = self.xml_toolkit.parse_xml_file(file_obj.file)
        self.assertIsNone(doc)
        self.assertEqual(result.status, XmlToolkitResultStatus.invalid_file)

    # Tests for valid xml, but does not comply with schema v2.1
    def test_valid_xml_but_invalid_schema(self):
        file_obj = File(os.path.join(self.cur_dir, "data/invalid_v21_doc.xml"))

        # Valid as xml
        doc, result = self.xml_toolkit.parse_xml_file(file_obj.file)
        self.assertIsNotNone(doc)
        self.assertEqual(result.status, XmlToolkitResultStatus.success)

        xmlschema = get_transxchange_schema(TXC_21)

        # Valid schema
        result = self.xml_toolkit.validate(doc, xmlschema)

        self.assertEqual(result.status, XmlToolkitResultStatus.schema_validation_failed)

    # Tests correct schema version 2.1 is selected
    def test_select_schema_21(self):
        # setup
        file_obj = File(
            os.path.join(self.cur_dir, "data/xml_with_schema_version_21_attribute.xml")
        )
        doc, result = self.xml_toolkit.parse_xml_file(file_obj.file)

        # test
        schema_version = self.xml_file_parser.check_schema(doc)

        # assert
        self.assertEqual("2.1", schema_version)

    # Tests correct schema version 2.4 is selected
    def test_select_schema_24(self):
        # setup
        file_obj = File(
            os.path.join(self.cur_dir, "data/xml_with_schema_version_24_attribute.xml")
        )
        doc, result = self.xml_toolkit.parse_xml_file(file_obj.file)

        # test
        schema_version = self.xml_file_parser.check_schema(doc)

        # assert
        self.assertEqual("2.4", schema_version)

    # An xml file with a missing SchemaVersion attribute should throw
    def test_select_schema_invalid(self):
        # setup
        file_obj = File(
            os.path.join(
                self.cur_dir, "data/xml_with_missing_schema_version_attribute.xml"
            )
        )
        doc, result = self.xml_toolkit.parse_xml_file(file_obj.file)

        # test
        self.assertRaises(Exception, self.xml_file_parser.check_schema(doc))

    # Tests xml is valid schema v2.1
    def test_valid_schema_21(self):
        file_obj = File(os.path.join(self.cur_dir, "data/ea_20-1A-A-y08-1.xml"))

        # Valid as xml
        doc, result = self.xml_toolkit.parse_xml_file(file_obj.file)
        self.assertIsNotNone(doc)
        self.assertEqual(result.status, XmlToolkitResultStatus.success)

        xmlschema = get_transxchange_schema(TXC_21)

        # Valid schema
        result = self.xml_toolkit.validate(doc, xmlschema)

        self.assertEqual(result.status, XmlToolkitResultStatus.success)

    # Tests xml is valid trans schema v2.4
    def test_valid_schema_24(self):
        file_obj = File(os.path.join(self.cur_dir, "data/valid_v24_doc.xml"))

        # Valid as xml
        doc, result = self.xml_toolkit.parse_xml_file(file_obj.file)
        self.assertIsNotNone(doc)
        self.assertEqual(result.status, XmlToolkitResultStatus.success)

        xmlschema = get_transxchange_schema(TXC_24)

        # Valid schema
        result = self.xml_toolkit.validate(doc, xmlschema)

        self.assertEqual(result.status, XmlToolkitResultStatus.success)
