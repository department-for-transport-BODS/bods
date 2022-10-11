from typing import List

from dateutil.parser import parse as parse_datetime_str
from lxml import etree

from transit_odp.common.xmlelements import XMLElement

NETEX_NAMESPACE_PREFIX = "netex"
NETEX_NAMESPACE = "http://www.netex.org.uk/netex"

class NeTExElement(XMLElement):

    namespaces = {NETEX_NAMESPACE_PREFIX: NETEX_NAMESPACE}

    def _make_xpath(self, xpath):
        if isinstance(xpath, (list, tuple)):
            xpath = [NETEX_NAMESPACE_PREFIX + ":" + path for path in xpath]
        else:
            xpath = NETEX_NAMESPACE_PREFIX + ":" + xpath
        return super()._make_xpath(xpath)


class NeTExDocument:
    def __init__(self, source):
        if hasattr(source, "seek"):
            source.seek(0)
        self._source = source
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

    def get_product_type(self):
        xpath = ["fareProducts", "PreassignedFareProduct", "ProductType"]
        elements = self.find_anywhere(xpath)
        return elements[0].text

    def get_tariff_time_intervals(self):
        xpath = ["tariffs", "Tariff", "timeIntervals", "TimeInterval", "Name"]
        elements = self.find_anywhere(xpath)
        print("TimeInterval>>>", elements[0].text)
        return elements[0].text

    # def fare_products(self):
    #     xpath = "fareProducts"
    #     products = self.find_anywhere(xpath)
    #     if len(products) > 0:
    #         return products[0].children
    #     else:
    #         return []