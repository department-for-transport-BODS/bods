import zipfile
from typing import List

from dateutil.parser import parse as parse_datetime_str
from lxml import etree

from transit_odp.common.xmlelements import XMLElement
from transit_odp.validate import XMLValidator
from transit_odp.validate.xml import validate_xml_files_in_zip

_NETEX_NAMESPACE_PREFIX = "netex"
_NETEX_NAMESPACE = "http://www.netex.org.uk/netex"
NETEX_SCHEMA_URL = "http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd"


class NeTExValidator(XMLValidator):
    def __init__(self, file, schema=NETEX_SCHEMA_URL, **kwargs):
        super().__init__(file, schema=schema, **kwargs)


class NeTExElement(XMLElement):
    """A wrapper class to easily work lxml elements for NeTEx XML.

    This adds the NeTEx namespaces to the XMLElement class.
    The NeTExDocument tree is traversed using the following general
    principle. Child elements are accessed via properties, e.g.
    FareZone elements are document.fare_zones.

    If you expect a bultin type to be returned this will generally
    be a getter method e.g. documents.get_scheduled_stop_points_ids()
    since this returns a list of strings.

    Args:
        root (etree._Element): the root of an lxml _Element.

    Example:
        # Traverse the tree
        >>> tree = etree.parse(netexfile)
        >>> netex = NeTExElement(tree.getroot())
        >>> netex.get_element("PublicationTimestamp")
            PublicationTimestamp(text='2119-06-22T13:51:43.044Z')
        >>> netex.get_elements(["dataObjects", "CompositeFrame"])
            [CompositeFrame(...), CompositeFrame(...)]
        >>> netex.get_elements(["dataObjects", "CompositeFrame", "Name"])
            [Name(...), Name(...)

        # Element attributes are accessed like dict values
        >>> netex["version"]
            '1.1'
    """

    namespaces = {_NETEX_NAMESPACE_PREFIX: _NETEX_NAMESPACE}

    def _make_xpath(self, xpath):
        if isinstance(xpath, (list, tuple)):
            xpath = [_NETEX_NAMESPACE_PREFIX + ":" + path for path in xpath]
        else:
            xpath = _NETEX_NAMESPACE_PREFIX + ":" + xpath
        return super()._make_xpath(xpath)


class NeTExDocument:
    def __init__(self, source):
        # sometimes the file might not point to beginning
        if hasattr(source, "seek"):
            source.seek(0)
        self._source = source
        # we do this since source can be a file or a str path
        self.name = getattr(source, "name", source)
        tree = etree.parse(source)
        self._root = NeTExElement(tree.getroot())

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}(source={self.name!r})"

    def __getattr__(self, attr):
        try:
            return getattr(self._root, attr)
        except AttributeError:
            msg = f"{self.__class__.__name__!r} has no attribute {attr!r}"
            raise AttributeError(msg)

    def get_netex_version(self):
        return self._root["version"]

    @property
    def fare_zones(self):
        xpath = "FareZone"
        return self.find_anywhere(xpath)

    @property
    def lines(self):
        xpath = "Line"
        return self.find_anywhere(xpath)

    @property
    def sales_offer_packages(self):
        xpath = "SalesOfferPackage"
        return self.find_anywhere(xpath)

    @property
    def fare_products(self):
        xpath = "fareProducts"
        products = self.find_anywhere(xpath)
        if len(products) > 0:
            return products[0].children
        else:
            return []

    @property
    def user_profiles(self):
        xpath = ["usageParameters", "UserProfile"]
        return self.find_anywhere(xpath)

    def get_earliest_tariff_from_date(self):
        xpath = ["Tariff", "validityConditions", "ValidBetween", "FromDate"]
        elements = self.find_anywhere(xpath)
        from_dates = [parse_datetime_str(from_date.text) for from_date in elements]

        if from_dates:
            return min(from_dates)

        return None

    def get_latest_tariff_to_date(self):
        xpath = ["Tariff", "validityConditions", "ValidBetween", "ToDate"]
        elements = self.find_anywhere(xpath)
        to_dates = [parse_datetime_str(to_date.text) for to_date in elements]
        if to_dates:
            return max(to_dates)

        return None

    @property
    def scheduled_stop_points(self):
        xpath = ["scheduledStopPoints", "ScheduledStopPoint"]
        elements = self.find_anywhere(xpath)
        return elements

    @property
    def scheduled_stop_point_refs(self):
        xpath = ["FareZone", "members", "ScheduledStopPointRef"]
        elements = self.find_anywhere(xpath)
        return elements

    def get_scheduled_stop_point_ref_ids(self):
        return [point["ref"] for point in self.scheduled_stop_point_refs]

    def get_scheduled_stop_point_ids(self):
        return [point["id"] for point in self.scheduled_stop_points]

    def get_topographic_place_ref_locality_ids(self) -> List[str]:
        xpath = [
            "scheduledStopPoints",
            "ScheduledStopPoint",
            "TopographicPlaceView",
            "TopographicPlaceRef",
        ]
        place_refs = self.find_anywhere(xpath)
        refs = [place_ref["ref"].split(":")[-1] for place_ref in place_refs]
        return refs


def get_documents_from_zip(zipfile_) -> List[NeTExDocument]:
    """Returns a list NeTExDocuments from a zip file."""
    docs = []
    with zipfile.ZipFile(zipfile_) as zout:
        filenames = [name for name in zout.namelist() if name.endswith("xml")]
        for name in filenames:
            with zout.open(name) as xmlout:
                docs.append(NeTExDocument(xmlout))
    return docs


def get_documents_from_file(source) -> List[NeTExDocument]:
    """Returns a list of NeTExDocuments from a file or filepath."""
    if zipfile.is_zipfile(source):
        return get_documents_from_zip(source)
    else:
        doc = NeTExDocument(source)
        return [doc]


def validate_netex_files_in_zip(zipfile_):
    return validate_xml_files_in_zip(zipfile_, schema=NETEX_SCHEMA_URL)
