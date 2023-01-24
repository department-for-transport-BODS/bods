import zipfile
from typing import List

from dateutil.parser import parse as parse_datetime_str
from django.conf import settings
from lxml import etree
from waffle import flag_is_active

from transit_odp.common.xmlelements import XMLElement
from transit_odp.pipelines.constants import SchemaCategory
from transit_odp.pipelines.models import SchemaDefinition
from transit_odp.pipelines.pipelines.xml_schema import SchemaLoader
from transit_odp.validate import XMLValidator

_NETEX_NAMESPACE_PREFIX = "netex"
_NETEX_NAMESPACE = "http://www.netex.org.uk/netex"
NETEX_SCHEMA_URL = "http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd"
NETEX_SCHEMA_ZIP_URL = settings.NETEX_SCHEMA_ZIP_URL
NETEX_XSD_PATH = settings.NETEX_XSD_PATH


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
        tree = etree.parse(netexfile)
        netex = NeTExElement(tree.getroot())
        netex.get_element("PublicationTimestamp")
            PublicationTimestamp(text='2119-06-22T13:51:43.044Z')
        netex.get_elements(["dataObjects", "CompositeFrame"])
            [CompositeFrame(...), CompositeFrame(...)]
        netex.get_elements(["dataObjects", "CompositeFrame", "Name"])
            [Name(...), Name(...)

        # Element attributes are accessed like dict values
        netex["version"]
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

    is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
    if is_fares_validator_active:

        def get_xml_file_name(self):
            xml_file_name = self.name
            return xml_file_name

        def get_multiple_attr_text_from_xpath(self, path):
            elements_list = self.find_anywhere(path)
            element_text = [element.text for element in elements_list]
            return element_text

        def get_multiple_attr_ids_from_xpath(self, path):
            elements_list = self.find_anywhere(path)
            element_id = [element["id"] for element in elements_list]
            return element_id

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

    def get_product_types(self):
        xpath = ["fareProducts", "PreassignedFareProduct", "ProductType"]
        return list(self.find_anywhere(xpath))

    def get_products_count(self, product_value_list):
        count = 0
        product_type_list = self.get_product_types()

        for product_type in product_type_list:
            if getattr(product_type, "text") in product_value_list:
                count += 1

        return count

    def get_number_of_trip_products(self):
        trip_product_values = [
            "singleTrip",
            "dayReturnTrip",
            "periodReturnTrip",
            "timeLimitedSingleTrip",
            "ShortTrip",
        ]
        trip_product_count = self.get_products_count(trip_product_values)
        return trip_product_count

    def get_number_of_pass_products(self):
        pass_product_values = ["dayPass", "periodPass"]
        pass_product_count = self.get_products_count(pass_product_values)
        return pass_product_count

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

    if is_fares_validator_active:

        def get_atco_area_code(self):
            path = ["scheduledStopPoints", "ScheduledStopPoint"]
            stop_point_elements = self.find_anywhere(path)
            stop_point_ids_list = [
                stop_point["id"] for stop_point in stop_point_elements
            ]
            all_atco_codes_list = [
                element_id.split(":")[-1] for element_id in stop_point_ids_list
            ]
            valid_atco_codes_list = [code[:3] for code in all_atco_codes_list]

            return valid_atco_codes_list

        def get_valid_from_date(self):
            path = ["CompositeFrame", "ValidBetween", "FromDate"]
            from_date_elements = self.find_anywhere(path)
            from_date_list = [
                str(parse_datetime_str(from_date.text))[:10]
                for from_date in from_date_elements
            ]
            return from_date_list

        def get_composite_frame_ids(self):
            path = ["CompositeFrame"]
            frame_elements = self.find_anywhere(path)
            composite_frame_ids = [frame["id"] for frame in frame_elements]
            return composite_frame_ids

        def get_to_date_texts(self):
            path = ["CompositeFrame", "ValidBetween", "ToDate"]
            to_date_elements_list = self.find_anywhere(path)
            all_to_date_text_list = [
                str(parse_datetime_str(to_date.text))[:10]
                for to_date in to_date_elements_list
            ]
            return all_to_date_text_list

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
            if not name.startswith("__"):
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


def get_netex_schema() -> etree.XMLSchema:
    """
    Helper method to return netex scheme object
    """
    definition = SchemaDefinition.objects.get(category=SchemaCategory.NETEX)
    schema_loader = SchemaLoader(definition, NETEX_XSD_PATH)
    return schema_loader.schema
