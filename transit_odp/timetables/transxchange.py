import logging
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import List, Optional

from lxml import etree
from pydantic import BaseModel

from transit_odp.common.utils import sha1sum
from transit_odp.common.xmlelements import XMLElement
from transit_odp.common.xmlelements.exceptions import NoElement
from transit_odp.timetables.constants import (
    TRANSXCAHNGE_NAMESPACE,
    TRANSXCHANGE_NAMESPACE_PREFIX,
)
from transit_odp.validate import ZippedValidator

logger = logging.getLogger(__name__)

GRID_LOCATION = "Grid"
WSG84_LOCATION = "WGS84"
PRINCIPAL_TIMING_POINTS = ["PTP", "principalTimingPoint"]


class TXCSchemaViolation(BaseModel):
    filename: str
    line: int
    details: str

    @classmethod
    def from_error(cls, error):
        filename = Path(error.filename).name
        return cls(filename=filename, line=error.line, details=error.message)


class TransXChangeElement(XMLElement):
    """A wrapper class to easily work lxml elements for TransXChange XML.

    This adds the TransXChange namespaces to the XMLElement class.
    The TransXChangeDocument tree is traversed using the following general
    principle. Child elements are accessed via properties, e.g.
    Service elements are document.services.

    If you expect a bultin type to be returned this will generally
    be a getter method e.g. documents.get_scheduled_stop_points_ids()
    since this returns a list of strings.

    Args:
        root (etree._Element): the root of an lxml _Element.

    Example:
        # Traverse the tree
        tree = etree.parse(netexfile)
        trans = TransXChangeDocument(tree.getroot())
        trans.get_element("PublicationTimestamp")
            PublicationTimestamp(text='2119-06-22T13:51:43.044Z')
        trans.get_elements(["dataObjects", "CompositeFrame"])
            [CompositeFrame(...), CompositeFrame(...)]
        trans.get_elements(["dataObjects", "CompositeFrame", "Name"])
            [Name(...), Name(...)

        # Element attributes are accessed like dict values
        trans["version"]
            '1.1'
    """

    namespaces = {TRANSXCHANGE_NAMESPACE_PREFIX: TRANSXCAHNGE_NAMESPACE}

    def _make_xpath(self, xpath):
        if isinstance(xpath, (list, tuple)):
            xpath = [TRANSXCHANGE_NAMESPACE_PREFIX + ":" + path for path in xpath]
        else:
            xpath = TRANSXCHANGE_NAMESPACE_PREFIX + ":" + xpath
        return super()._make_xpath(xpath)


class TransXChangeDocument:
    """A class for handling and validating TransXChange XML Documents."""

    def __init__(self, source):
        """Initialise class.

        Args:
            source (path|file|url): Something that can parsed by `lxml.etree.parse`.

        """
        self.hash = None
        if hasattr(source, "seek"):
            source.seek(0)
            self.hash = sha1sum(source.read())
            source.seek(0)
        self.source = source
        self.name = getattr(source, "name", source)
        self._tree = etree.parse(self.source)
        self._root = TransXChangeElement(self._tree.getroot())

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}(source={self.name!r})"

    def __getattr__(self, attr):
        try:
            return getattr(self._root, attr)
        except AttributeError:
            msg = f"{self.__class__.__name__!r} has no attribute {attr!r}"
            raise AttributeError(msg)

    def get_transxchange_version(self):
        """Get the TransXChangeDocuments schema version."""
        return self._root["SchemaVersion"]

    def get_location_system(self):
        """Gets the location system used by the TxC file.

        Returns:
            str or None: If LocationSystem exists return text, else return None.
        """
        element = self._root.get_element_or_none("LocationSystem")

        if element:
            return element.text

        if self.has_latitude():
            return WSG84_LOCATION

        return GRID_LOCATION

    def get_creation_date_time(self):
        """Gets the CreationDateTime attribute from TxC file.

        Returns:
            str or None: If CreationDateTime exists return str, else return None.
        """
        return self._root["CreationDateTime"]

    def get_modification_date_time(self):
        """Gets the ModificationDateTime attribute from TxC file.

        Returns:
            str or None: If ModificationDateTime exists return str, else return None.
        """
        return self._root["ModificationDateTime"]

    def get_revision_number(self) -> str:
        """Gets the RevisionNumber attribute from a TxC file.

        Returns:
            str: Returns the value in RevisionNumber.
        """
        return self._root["RevisionNumber"]

    def get_file_name(self) -> str:
        """
        Gets the FileName attribute from a TxC file.

        Returns:
            str: Returns the value in FileName.

        """
        return self._root.get("FileName", "")

    def get_modification(self) -> str:
        """
        Gets the Modification attribute from a TxC file.

        Returns:
            str: Returns the value in Modification.

        """
        return self._root["Modification"]

    def get_services(self):
        """Get all the Service elements in the TransXChangeDocument.

        Returns:
            List[TransXChangeElement]: A list of TransXChangeElement Service elements.
        """
        xpath = ["Services", "Service"]
        return self.find_anywhere(xpath)

    def get_service_codes(self):
        xpath = ["Services", "Service", "ServiceCode"]
        return self.find_anywhere(xpath)

    def get_lines(self):
        """Get all the Line elements in the TransXChangeDocument.

        Returns:
            List[TransXChangeElement]: A list of TransXChangeElement Line elements.
        """
        xpath = ["Services", "Service", "Lines", "Line"]
        return self.find_anywhere(xpath)

    def get_all_line_names(self):
        """Get the text of all the LineName elements in the TransXChangeDocument.

        Returns:
            List[str]: A list of the line names.
        """
        xpath = ["Services", "Service", "Lines", "Line", "LineName"]
        return [name.text for name in self.find_anywhere(xpath)]

    def get_annotated_stop_point_refs(self):
        """Get all the AnnotatedStopPointRef elements in the TransXChangeDocument.

        Returns:
            List[TransXChangeElement]: A list of TransXChangeElement
            AnnotatedStopPointRef elements.
        """
        xpath = ["StopPoints", "AnnotatedStopPointRef"]
        return self.find_anywhere(xpath)

    def get_stop_points(self):
        """Get all the StopPoint elements in the TransXChangeDocument.

        Returns:
            List[TransXChangeElement]: A list of TransXChangeElement StopPoint elements.
        """
        xpath = ["StopPoints", "StopPoint"]
        return self.find_anywhere(xpath)

    def has_latitude(self):
        """Check if the first stop point contains a latitude element.

        Returns:
            bool: If StopPoint < Place < Location has a Latitude element return True
            else False.
        """
        xpath = ["StopPoints", "StopPoint", "Place", "Location"]
        locations = self.find_anywhere(xpath)

        if len(locations) == 0:
            return False

        try:
            locations[0].get_elements("Latitude")
            return True
        except NoElement:
            return False

    def get_journey_pattern_sections(self):
        """Get all the JourneyPatternSection elements in the TransXChangeDocument.

        Returns:
            List[TransXChangeElement]: A list of TransXChangeElement
            JourneyPatternSection elements.
        """
        xpath = ["JourneyPatternSections", "JourneyPatternSection"]
        return self._root.get_elements(xpath)

    def get_operators(self):
        xpath = ["Operators", "Operator"]
        return self.find_anywhere(xpath)

    def get_licensed_operators(self):
        xpath = ["Operators", "LicensedOperator"]
        return self.find_anywhere(xpath)

    def get_nocs(self) -> List[str]:
        xpath = "NationalOperatorCode"
        return [noc.text for noc in self.find_anywhere(xpath)]

    def get_principal_timing_points(self) -> List[TransXChangeElement]:
        xpath = "TimingStatus"
        return [
            s for s in self.find_anywhere(xpath) if s.text in PRINCIPAL_TIMING_POINTS
        ]

    def get_operating_period_start_date(self) -> Optional[TransXChangeElement]:
        xpath = ["Services", "Service", "OperatingPeriod", "StartDate"]
        return self.find_anywhere(xpath)

    def get_operating_period_end_date(self) -> Optional[TransXChangeElement]:
        xpath = ["Services", "Service", "OperatingPeriod", "EndDate"]
        return self.find_anywhere(xpath)

    def get_public_use(self) -> Optional[TransXChangeElement]:
        xpath = ["Services", "Service", "PublicUse"]
        return self.find_anywhere(xpath)

    def get_service_origin(self) -> str:
        """
        Returns the Origin text of a Service.
        """
        flexible = ["Services", "Service", "FlexibleService", "Origin"]
        origin = self._root.get_first_text_or_default(xpath=flexible, default="")
        if origin:
            return origin

        standard = ["Services", "Service", "StandardService", "Origin"]
        origin = self._root.get_first_text_or_default(xpath=standard, default="")
        return origin

    def get_service_destination(self) -> str:
        """
        Returns the Destination of a Service.
        """
        flexible = ["Services", "Service", "FlexibleService", "Destination"]
        destination = self._root.get_first_text_or_default(xpath=flexible, default="")
        if destination:
            return destination

        standard = ["Services", "Service", "StandardService", "Destination"]
        destination = self._root.get_first_text_or_default(xpath=standard, default="")
        return destination

    def get_vehicle_journeys(self):
        """Get all the VehicleJourney elements in the TransXChangeDocument.

        Returns:
            List[TransXChangeElement]: A list of TransXChangeElement
            VehicleJourney elements.
        """
        xpath = ["VehicleJourneys", "VehicleJourney"]
        return self._root.get_elements(xpath)

    def get_serviced_organisations(self):
        """
        Get all Serviced Organisations
        """
        xpath = ["ServicedOrganisations", "ServicedOrganisation"]
        return self._root.get_elements(xpath)


class TransXChangeZip(ZippedValidator):
    """A class for working with a zip file containing transxchange files."""

    def __init__(self, source):
        if not hasattr(source, "seek"):
            f_ = open(source, "rb")
        else:
            f_ = source
        super().__init__(f_)
        self._schema_21 = None
        self._schema_24 = None
        self.docs = []

    def get_transxchange_docs(self, validate=False):
        """Get all the TransXChangeDocuments in a zip file.

        Args:
            validate (bool): Validate the document against a TxC schema.

        Return:
            List[TransXChangeDocument]: A list of TransXChangeDocuments
        """
        filenames = self.get_files()
        docs = []
        for name in filenames:
            doc = self.get_doc_from_name(name, validate=validate)
            docs.append(doc)
        return docs

    def iter_doc(self):
        """Returns an Iterator of TransXChangeDocuments in a zip file.

        Args:
            validate (bool): Validate the document against a TxC schema.

        Return Iterator[TransXChangeDocuments]: An iterator of TransXChangeDocuments.
        """
        filenames = self.get_files()
        return (self.get_doc_from_name(n) for n in filenames)

    def get_doc_from_name(self, name):
        """Get a TransXChangeDocument from a zip file by name.

        Args:
            name (str): Name of file to retrieve
            validate (bool): Validate the document against a TxC schema.

        Return:
            TransXChangeDocument: The TransXChangeDocument with name

        """
        with self.open(name) as f_:
            doc = TransXChangeDocument(f_)
        return doc

    def validate_contents(self):
        """Validates the contents of the zip file.

        Returns:
            None: None is return if the contents are all valid TxC files.

        Raises:
            XMLValidationException: if a DocumentInvalid exception is raised.

        """
        filenames = self.get_files()
        count = len(filenames)
        logger.info(f"[TransXChange] Validating {count} files.")
        for ind, name in enumerate(filenames, start=1):
            logger.info(f"[TransXChange] => Validating {name} file {ind} of {count}.")
            self.get_doc_from_name(name)

    def validate(self):
        """Validate a zip file and then validate it's contents.

        Returns:
            None: If Zip and TransXChangeDocuments are all valid.

        Raises:
            NestedZipForbidden: if zip file contains another zip file.
            ZipTooLarge: if zip file or sum of uncompressed files are
            greater than max_file_size.
            NoDataFound: if zip file contains no files with data_file_ext extension.
            XMLValidationException: if a DocumentInvalid exception is raised.
        """
        super().validate()
        self.validate_contents()


class TransXChangeDatasetParser:
    """Class for iterating over transxchange file/s."""

    def __init__(self, source):
        self._source = source

    def is_zipfile(self) -> bool:
        return zipfile.is_zipfile(self._source)

    def _iter_docs(self):
        if self.is_zipfile():
            with TransXChangeZip(self._source) as zip_:
                for doc in zip_.iter_doc():
                    yield doc
        else:
            yield TransXChangeDocument(self._source)

    def get_documents(self) -> Iterator[TransXChangeDocument]:
        if self.is_zipfile():
            with TransXChangeZip(self._source) as zip_:
                for doc in zip_.iter_doc():
                    yield doc
        else:
            yield TransXChangeDocument(self._source)

    def get_transxchange_versions(self) -> List[TransXChangeElement]:
        return [doc.get_transxchange_version() for doc in self.get_documents()]

    def get_stop_points(self):
        all_stops = []
        for doc in self.get_documents():
            all_stops += doc.get_stop_points()
        return all_stops

    def get_annotated_stop_point_refs(self) -> List[TransXChangeElement]:
        all_stops = []
        for doc in self.get_documents():
            all_stops += doc.get_annotated_stop_point_refs()
        return all_stops

    def get_principal_timing_points(self) -> List[TransXChangeElement]:
        timing_points = []
        for doc in self.get_documents():
            timing_points += doc.get_principal_timing_points()
        return timing_points

    def get_nocs(self) -> List[str]:
        nocs = []
        for doc in self.get_documents():
            nocs += doc.get_nocs()
        return nocs

    def get_line_names(self):
        line_names = []
        for doc in self.get_documents():
            line_names += doc.get_all_line_names()

        return line_names
