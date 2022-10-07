from typing import List

from dateutil.parser import parse as parse_datetime_str
from lxml import etree

from transit_odp.common.xmlelements import XMLElement

NETEX_NAMESPACE_PREFIX = "netex"
NETEX_NAMESPACE = "http://www.netex.org.uk/netex"

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

    namespaces = {NETEX_NAMESPACE_PREFIX: NETEX_NAMESPACE}

    def _make_xpath(self, xpath):
        if isinstance(xpath, (list, tuple)):
            xpath = [NETEX_NAMESPACE_PREFIX + ":" + path for path in xpath]
        else:
            xpath = NETEX_NAMESPACE_PREFIX + ":" + xpath
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