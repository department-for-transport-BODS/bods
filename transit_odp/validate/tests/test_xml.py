import pytest
from defusedxml import DefusedXmlException
from defusedxml.ElementTree import ParseError
from lxml import etree

from transit_odp.validate.tests.utils import (
    create_sparse_file,
    create_text_file,
    create_zip_file,
)
from transit_odp.validate.xml import (
    DangerousXML,
    FileTooLarge,
    XMLSyntaxError,
    XMLValidator,
    validate_xml_files_in_zip,
)

TEST_SCHEMA = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">

<xs:element name="root">
  <xs:complexType>
    <xs:sequence>
      <xs:element name="child" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
</xs:schema>
"""


@pytest.mark.parametrize(
    "file_size,limit,expected",
    [(int(1e3), int(1e4), False), (int(1e3), int(1e2), True)],
)
def test_is_too_large(file_size, limit, expected, tmp_path):
    """Test file size checks."""

    file1 = tmp_path / "file.xml"
    create_sparse_file(file1, file_size)

    with open(file1, "rb") as f:
        validator = XMLValidator(f, max_file_size=limit)
        assert validator.is_too_large() == expected


def test_file_too_large_exception(tmp_path):
    """Test file too large exception is correctly thrown."""

    file1 = tmp_path / "file.xml"
    create_sparse_file(file1, 100)

    with open(file1, "rb") as f:
        validator = XMLValidator(f, max_file_size=10)
        with pytest.raises(FileTooLarge) as excinfo:
            validator.validate()

        assert str(excinfo.value.filename) == str(file1)


def test_get_document(tmp_path):
    """Test that valid XML can be parsed."""
    file1 = tmp_path / "file1.xml"
    xml_str = "<Root><Child>hello,world</Child></Root>"
    create_text_file(file1, xml_str)

    with open(file1, "rb") as f:
        validator = XMLValidator(f)
        doc = validator.get_document()
        assert etree.tostring(doc).decode("utf-8") == xml_str


def test_get_document_with_schema(tmp_path):
    """Test that valid XML can be parsed, with a schema."""
    file1 = tmp_path / "file1.xml"
    xml_declaration = '<?xml version="1.0"?>'
    xml_str = "<root><child>hello,world</child></root>"
    create_text_file(file1, xml_declaration + xml_str)
    schema1 = tmp_path / "schema.xml"
    create_text_file(schema1, TEST_SCHEMA)

    with open(file1, "rb") as f, open(schema1, "rb") as schema:
        validator = XMLValidator(f, schema=schema)
        doc = validator.get_document()
        assert etree.tostring(doc).decode("utf-8") == xml_str


def test_get_document_with_schema_exception(tmp_path):
    """Test that an XML with an invalid schema raises exception."""
    file1 = tmp_path / "file1.xml"
    xml_declaration = '<?xml version="1.0"?>'
    xml_str = "<root><branch>hello,world</branch></root>"
    create_text_file(file1, xml_declaration + xml_str)
    schema1 = tmp_path / "schema.xml"
    create_text_file(schema1, TEST_SCHEMA)

    with open(file1, "rb") as f, open(schema1, "rb") as schema:
        validator = XMLValidator(f, schema=schema)
        with pytest.raises(XMLSyntaxError):
            validator.get_document()


def test_get_document_exception(tmp_path):
    """Test that exception is raised when file contains invalid XML."""
    file1 = tmp_path / "file1.xml"
    not_xml_str = "hello,world"
    create_text_file(file1, not_xml_str)

    with open(file1, "rb") as f:
        validator = XMLValidator(f)
        with pytest.raises(XMLSyntaxError) as excinfo:
            validator.get_document()

        assert str(excinfo.value.filename) == str(file1)


def test_dangerouse_xml_exception(tmp_path, mocker):
    """Test that correct exception is raised when DefusedXmlException is thrown."""
    parse = "transit_odp.validate.xml.detree.parse"
    mocker.patch(parse, side_effect=DefusedXmlException)

    file1 = tmp_path / "file1.xml"
    create_sparse_file(file1, file_size=int(1e2))

    with open(file1, "rb") as f:
        validator = XMLValidator(f)
        with pytest.raises(DangerousXML) as excinfo:
            validator.validate()

        assert str(excinfo.value.filename) == str(file1)


def test_parse_error_exception(tmp_path, mocker):
    """Test that correct exception is raised when ParseError is thrown."""

    parse = "transit_odp.validate.xml.detree.parse"
    mocker.patch(parse, side_effect=ParseError)

    file1 = tmp_path / "file1.xml"
    create_sparse_file(file1, file_size=int(1e2))

    with open(file1, "rb") as f:
        validator = XMLValidator(f)
        with pytest.raises(XMLSyntaxError) as excinfo:
            validator.validate()

        assert str(excinfo.value.filename) == str(file1)


def test_validate_xmls_from_zip_valid(tmp_path):
    filenames = [tmp_path / f"file{i}.xml" for i in range(1, 3)]
    xml_str = "<Root><Child>hello,world</Child></Root>"
    for filename in filenames:
        create_text_file(filename, xml_str)

    zip_filename = tmp_path / "zipfile.zip"
    create_zip_file(zip_filename, filenames)
    with open(zip_filename, "rb") as zout:
        validate_xml_files_in_zip(zout)


def test_validate_xmls_from_zip_invalid_file(tmp_path):
    filenames = [tmp_path / f"file{i}.xml" for i in range(1, 3)]
    xml_str = "<Root><Child>hello,world</Child></Root>"
    for filename in filenames:
        create_text_file(filename, xml_str)

    not_xml_file = tmp_path / "notxml.xml"
    create_sparse_file(not_xml_file, 100)
    filenames.append(not_xml_file)

    zip_filename = tmp_path / "zipfile.zip"
    create_zip_file(zip_filename, filenames)
    with open(zip_filename, "rb") as zout:
        with pytest.raises(XMLSyntaxError):
            validate_xml_files_in_zip(zout)
