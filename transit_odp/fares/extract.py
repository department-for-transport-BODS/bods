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
        try:
            min_date = min(
                doc.get_earliest_tariff_from_date() for doc in self.documents
            )
        except TypeError:
            return None
        return min_date

    @property
    def valid_to(self):
        try:
            max_date = max(doc.get_latest_tariff_to_date() for doc in self.documents)
        except TypeError:
            return None
        return max_date

    @property
    def stop_point_refs(self):
        stop_point_refs = [
            doc.get_scheduled_stop_point_ref_ids() for doc in self.documents
        ]
        return list(itertools.chain(*stop_point_refs))

    @property
    def xml_file_name(self):
        xml_file_name = [doc.get_xml_file_name() for doc in self.documents]
        return xml_file_name

    @property
    def fares_valid_from(self):
        try:
            valid_from = [doc.get_valid_from_date() for doc in self.documents].pop()
        except IndexError:
            return None

        return valid_from

    @property
    def fares_valid_to(self):
        try:
            composite_frame_ids_list = [
                doc.get_composite_frame_ids() for doc in self.documents
            ].pop()
            to_date_text_list = [
                doc.get_to_date_texts() for doc in self.documents
            ].pop()
            if (
                len(to_date_text_list) > 1
                and "UK_PI_METADATA_OFFER" not in composite_frame_ids_list
            ):
                first_to_date_element = str(to_date_text_list[0])
                valid_to = first_to_date_element[:10]
                return valid_to
            else:
                return None
        except IndexError:
            return None

    @property
    def national_operator_code(self):
        try:
            path = ["organisations", "Operator", "PublicCode"]
            national_operator_code = [
                doc.get_multiple_attr_text_from_xpath(path) for doc in self.documents
            ].pop()
        except IndexError:
            return None

        return national_operator_code

    @property
    def tariff_basis(self):
        try:
            path = ["Tariff", "TariffBasis"]
            tariff_basis = [
                doc.get_multiple_attr_text_from_xpath(path) for doc in self.documents
            ].pop()
        except IndexError:
            return None

        return tariff_basis

    @property
    def product_type(self):
        try:
            path = ["fareProducts", "PreassignedFareProduct", "ProductType"]
            product_type = [
                doc.get_multiple_attr_text_from_xpath(path) for doc in self.documents
            ].pop()
        except IndexError:
            return None

        return product_type

    @property
    def product_name(self):
        try:
            path = ["fareProducts", "PreassignedFareProduct", "Name"]
            product_name = [
                doc.get_multiple_attr_text_from_xpath(path) for doc in self.documents
            ].pop()
        except IndexError:
            return None

        return product_name

    @property
    def user_type(self):
        try:
            path = [
                "FareStructureElement",
                "GenericParameterAssignment",
                "limitations",
                "UserProfile",
                "UserType",
            ]
            user_type = [
                doc.get_multiple_attr_text_from_xpath(path) for doc in self.documents
            ].pop()
        except IndexError:
            return None

        return user_type

    @property
    def line_id(self):
        try:
            path = ["lines", "Line"]
            line_ids = [
                doc.get_multiple_attr_ids_from_xpath(path) for doc in self.documents
            ].pop()
        except IndexError:
            return None

        return line_ids

    @property
    def line_name(self):
        try:
            path = ["lines", "Line", "PublicCode"]
            line_name = [
                doc.get_multiple_attr_text_from_xpath(path) for doc in self.documents
            ].pop()
        except IndexError:
            return None

        return line_name

    @property
    def atco_area(self):
        try:
            scheduled_stop_points = [
                doc.get_atco_area_code() for doc in self.documents
            ].pop()
        except IndexError:
            return None

        return scheduled_stop_points

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
            "xml_file_name",
            "fares_valid_from",
            "fares_valid_to",
            "national_operator_code",
            "line_id",
            "line_name",
            "atco_area",
            "tariff_basis",
            "product_type",
            "product_name",
            "user_type",
        ]
        try:
            data = {key: getattr(self, key) for key in keys}
        except ValueError as err:
            msg = "Unable to extract data from NeTEx file."
            raise ExtractionError(msg) from err

        return data
