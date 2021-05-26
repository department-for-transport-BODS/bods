import itertools
from typing import List

from transit_odp.fares.netex import NeTExDocument

NeTExDocuments = List[NeTExDocument]


class ExtractionError(Exception):
    """Generic exception for extraction errors."""

    code = "SYSTEM_ERROR"

    def __init__(self, message):
        self.message = message


class NeTExDocumentsExtractor:
    def __init__(self, documents: NeTExDocuments):
        self.documents = documents

    def _attr_from_documents(self, attr):
        """Iterates over all documents and gets `attr`."""
        elements = [getattr(doc, attr) for doc in self.documents]
        return elements

    def _get_count(self, attr):
        """Gets the total counts of an `attr` in all documents."""
        lens = [len(lines) for lines in self._attr_from_documents(attr)]
        return sum(lens)

    @property
    def schema_version(self):
        return min(doc.get_netex_version() for doc in self.documents)

    @property
    def num_of_lines(self):
        attr = "lines"
        return self._get_count(attr)

    @property
    def num_of_fare_zones(self):
        attr = "fare_zones"
        return self._get_count(attr)

    @property
    def num_of_sales_offer_packages(self):
        attr = "sales_offer_packages"
        return self._get_count(attr)

    @property
    def num_of_fare_products(self):
        attr = "fare_products"
        return self._get_count(attr)

    @property
    def num_of_user_profiles(self):
        attr = "user_profiles"
        return self._get_count(attr)

    @property
    def valid_from(self):
        return min(doc.get_earliest_tariff_from_date() for doc in self.documents)

    @property
    def valid_to(self):
        return max(doc.get_latest_tariff_to_date() for doc in self.documents)

    @property
    def stop_point_refs(self):
        stop_point_refs = [
            doc.get_scheduled_stop_point_ref_ids() for doc in self.documents
        ]
        return list(itertools.chain(*stop_point_refs))

    def to_dict(self):
        keys = [
            "schema_version",
            "num_of_lines",
            "num_of_fare_zones",
            "num_of_sales_offer_packages",
            "num_of_fare_products",
            "num_of_user_profiles",
            "valid_from",
            "valid_to",
            "stop_point_refs",
        ]
        try:
            data = {key: getattr(self, key) for key in keys}
        except ValueError as err:
            msg = "Unable to extract data from NeTEx file."
            raise ExtractionError(msg) from err

        return data
