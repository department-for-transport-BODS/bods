import logging
import zipfile

from defusedxml import DefusedXmlException
from defusedxml import ElementTree as detree
from defusedxml.ElementTree import ParseError
from lxml import etree
from ddtrace import tracer

from transit_odp.validate.exceptions import ValidationException
from transit_odp.common.loggers import DatasetPipelineLoggerContext, PipelineAdapter

from transit_odp.validate.utils import get_file_size

logger = logging.getLogger(__name__)


class XMLValidationException(ValidationException):
    code = "XML_VALIDATION_ERROR"
    message_template = "Unable to validate xml in {filename}."


class FileTooLarge(XMLValidationException):
    code = "FILE_TOO_LARGE"
    message_template = "XML file {filename} is too large."


class XMLSyntaxError(XMLValidationException):
    code = "XML_SYNTAX_ERROR"
    message_template = "File {filename} is not valid XML."


class DangerousXML(XMLValidationException):
    code = "DANGEROUS_XML_ERROR"
    message_template = "XML file {filename} contains dangerous XML."


class FileValidator:
    def __init__(self, source, max_file_size=10e9):
        self.source = source
        if self.is_file:
            self.source.seek(0)
        self.max_file_size = max_file_size

    @property
    def is_file(self):
        return hasattr(self.source, "seek")

    def is_too_large(self):
        if self.is_file:
            size_ = get_file_size(self.source)
        else:
            with open(self.source, "rb") as f_:
                size_ = get_file_size(f_)

        return size_ > self.max_file_size

    def validate(self):
        """Validates the file.

        Raises:
            FileTooLarge: if file size is greater than max_file_size.
        """
        if self.is_too_large():
            raise FileTooLarge(self.source.name)


class XMLValidator(FileValidator):
    """Class for validating a XML file.

    Args:
        file (File): A file-like object.
        max_file_size (int): The max file size allowed. default is 1 Gigabyte.

    Examples:
        >>> f = open("./path/to/xml/file.xml", "rb")
        >>> validator = XMLValidator(f)
        >>> validator.is_too_large()
            False
        >>> validator.validate()
        >>> f.close()
    """

    def __init__(self, source, max_file_size=5e9, schema=None):
        super().__init__(source, max_file_size=max_file_size)
        self.schema = schema

    def dangerous_xml_check(self):
        try:
            detree.parse(
                self.source, forbid_dtd=True, forbid_entities=True, forbid_external=True
            )
        except ParseError as err:
            # DefusedXml wraps ExpatErrors in ParseErrors, requires extra step to
            # get actual error message
            if isinstance(err.msg, Exception):
                raise XMLSyntaxError(self.source.name, message=err.msg.args[0]) from err
            else:
                raise XMLSyntaxError(self.source.name, message=err.msg) from err
        except DefusedXmlException as err:
            raise DangerousXML(self.source.name) from err

    def validate(self):
        """Validates the XML file.

        Raises:
            FileTooLarge: if file size is greater than max_file_size.
            DangerousXML: if DefusedXmlException is raised during parsing.
            XMLSyntaxError: if the file cannot be parsed.
        """
        if self.is_too_large():
            raise FileTooLarge(self.source.name)
        self.dangerous_xml_check()
        self.get_document()

    def get_document(self):
        """Parses `file` returning an lxml element object.
        If `schema` is not None then `file` is validated against the schema.

        Returns:
           doc(_ElementTree): an lxml element tree representing the document.

        Raises:
            lxml.XMLSyntaxError: if contents of `file` do not match the `schema`
        """
        if self.is_file:
            self.source.seek(0)
        parser = None
        if self.schema is not None:
            lxml_schema = get_lxml_schema(self.schema)
            parser = etree.XMLParser(schema=lxml_schema)
        try:
            doc = etree.parse(self.source, parser)
        except etree.XMLSyntaxError as err:
            raise XMLSyntaxError(self.source.name, message=err.msg) from err
        return doc


@tracer.wrap(service="Publish", resource="validate_xml_files_in_zip")
def validate_xml_files_in_zip(zip_file, schema=None):
    """Validate all the xml files in a zip archive."""
    context = DatasetPipelineLoggerContext(component_name="FaresPipeline")
    adapter = PipelineAdapter(logger, {"context": context})
    with zipfile.ZipFile(zip_file) as zout:
        filenames = [name for name in zout.namelist() if name.endswith("xml")]
        lxml_schema = get_lxml_schema(schema)
        total_files = len(filenames)
        for index, name in enumerate(filenames, 1):
            adapter.info(f"XML Validation of file {index} of {total_files} - {name}.")
            with zout.open(name) as xmlout:
                XMLValidator(xmlout, schema=lxml_schema).validate()


def get_lxml_schema(schema):
    """Creates an lxml XMLSchema object from a file, file path or url."""
    if schema is None:
        return

    if not isinstance(schema, etree.XMLSchema):
        logger.info(f"[XML] => Parsing {schema}.")
        root = etree.parse(schema)
        schema = etree.XMLSchema(root)
    return schema
