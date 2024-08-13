import os
import zipfile

import psutil
from celery.utils.log import get_task_logger

from transit_odp.fares.netex import NeTExDocument, get_documents_from_file
from transit_odp.pipelines import exceptions

logger = get_task_logger(__name__)


def measure_memory(func):
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())
        before = process.memory_info().rss
        result = func(*args, **kwargs)
        after = process.memory_info().rss
        print(f"Memory used by {func.__name__}: {after - before} bytes")
        return result

    return wrapper


class ExtractionError(Exception):
    """Generic exception for extraction errors."""

    code = "SYSTEM_ERROR"

    def __init__(self, message):
        self.message = message


class FaresDataCatalogueExtractor:
    def __init__(self, documents: NeTExDocument):
        self.documents = documents

    @property
    def xml_file_name(self):
        xml_file_name = self.documents.get_xml_file_name()
        return xml_file_name

    @property
    def valid_from(self):
        try:
            composite_frame_ids_list = self.documents.get_composite_frame_ids()
            valid_from_list = self.documents.get_valid_from_date()
            if len(valid_from_list) == 1 and any(
                "UK_PI_METADATA_OFFER" in sub for sub in composite_frame_ids_list
            ):
                return None
            return valid_from_list[0]
        except IndexError:
            return None

    @property
    def valid_to(self):
        try:
            composite_frame_ids_list = self.documents.get_composite_frame_ids()
            to_date_text_list = self.documents.get_to_date_texts()
            if len(to_date_text_list) == 1 and any(
                "UK_PI_METADATA_OFFER" in sub for sub in composite_frame_ids_list
            ):
                return None
            return to_date_text_list[0]
        except IndexError:
            return None

    @property
    def national_operator_code(self):
        try:
            path = [
                "CompositeFrame[not(contains(@id, 'METADATA'))]",
                "frames",
                "ResourceFrame",
                "organisations",
                "Operator",
                "PublicCode",
            ]
            national_operator_code_list = (
                self.documents.get_multiple_attr_text_from_xpath(path)
            )

            if national_operator_code_list:
                return national_operator_code_list
            return []
        except IndexError:
            return []

    @property
    def tariff_basis(self):
        try:
            path = ["Tariff", "TariffBasis"]
            tariff_basis_list = self.documents.get_multiple_attr_text_from_xpath(path)
            if tariff_basis_list:
                return list(dict.fromkeys(tariff_basis_list))
            return []
        except IndexError:
            return []

    @property
    def product_type(self):
        try:
            path = ["fareProducts", "PreassignedFareProduct", "ProductType"]
            product_type_list = self.documents.get_multiple_attr_text_from_xpath(path)

            if product_type_list:
                return list(dict.fromkeys(product_type_list))
            return []
        except IndexError:
            return []

    @property
    def product_name(self):
        try:
            path = ["fareProducts", "PreassignedFareProduct", "Name"]
            product_name_list = self.documents.get_multiple_attr_text_from_xpath(path)

            if product_name_list:
                return list(dict.fromkeys(product_name_list))
            return []
        except IndexError:
            return []

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
            user_type_list = self.documents.get_multiple_attr_text_from_xpath(path)

            if user_type_list:
                return list(dict.fromkeys(user_type_list))
            return []
        except IndexError:
            return []

    @property
    def line_id(self):
        try:
            path = ["lines", "Line"]
            line_ids_list = self.documents.get_multiple_attr_ids_from_xpath(path)
            if line_ids_list:
                return list(dict.fromkeys(line_ids_list))
            return []
        except IndexError:
            return []

    @property
    def line_name(self):
        try:
            path = ["lines", "Line", "PublicCode"]
            line_name_list = self.documents.get_multiple_attr_text_from_xpath(path)
            if line_name_list:
                return list(dict.fromkeys(line_name_list))
            return []
        except IndexError:
            return []

    @property
    def atco_area(self):
        try:
            scheduled_stop_points_list = self.documents.get_atco_area_code()
            if scheduled_stop_points_list:
                return list(dict.fromkeys(scheduled_stop_points_list))
            return []
        except IndexError:
            return []

    def to_dict(self):
        keys = [
            "xml_file_name",
            "valid_from",
            "valid_to",
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


class NeTExDocumentsExtractor:
    def __init__(self, revision):
        self.doc = NeTExDocument
        self.revision = revision
        self.fares_catalogue_extracted_data = []

    def _attr_from_documents(self, attr):
        """Iterates over all documents and gets `attr`."""
        elements = getattr(self.doc, attr)
        return elements

    def _get_count(self, attr):
        """Gets the total counts of an `attr` in all documents."""
        return len(self._attr_from_documents(attr))

    def _get_user_type(self, attr):
        """Gets the total count of distinct UserType in all documents"""
        lists_user_types = self._attr_from_documents(attr)
        distinct_user_types = set(lists_user_types)
        return distinct_user_types

    @property
    def schema_version(self):
        return float(self.doc.get_netex_version())

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
        return self._get_user_type(attr)

    @property
    def valid_from(self):
        try:
            min_date = self.doc.get_earliest_tariff_from_date()
        except TypeError:
            return None
        return min_date

    @property
    def valid_to(self):
        try:
            max_date = self.doc.get_latest_tariff_to_date()
        except TypeError:
            return None
        return max_date

    @property
    def stop_point_refs(self):
        return self.doc.get_scheduled_stop_point_ref_ids()

    @property
    def num_of_trip_products(self):
        trip_products_list = []
        product_type_list = self.doc.get_product_types()
        trip_product_values = [
            "singleTrip",
            "dayReturnTrip",
            "periodReturnTrip",
            "timeLimitedSingleTrip",
            "ShortTrip",
        ]
        for product_type in product_type_list:
            if getattr(product_type, "text") in trip_product_values:
                trip_products_list.append(getattr(product_type, "text"))
        return set(trip_products_list)

    @property
    def num_of_pass_products(self):
        pass_products_list = []
        product_type_list = self.doc.get_product_types()
        pass_product_values = ["dayPass", "periodPass"]

        for product_type in product_type_list:
            if getattr(product_type, "text") in pass_product_values:
                pass_products_list.append(getattr(product_type, "text"))
        return set(pass_products_list)

    @property
    def fares_data_catalogue(self):
        fares_catalogue = FaresDataCatalogueExtractor(self.doc)
        self.fares_catalogue_extracted_data.append(fares_catalogue.to_dict())
        return self.fares_catalogue_extracted_data

    @measure_memory
    def extract(self):
        """
        Processes a zip file.
        """
        extracts_sum = []
        extracts_distinct_count = []
        extracts_min = []
        extracts_max = []
        extracts_list = []
        extracts_fares_data_catalogue = []

        final_dictionary_sum = dict()
        final_dictionary_dictinct_count = dict()
        final_dictionary_min = dict()
        final_dictionary_max = dict()
        final_dictionary_list = dict()

        documents = get_documents_from_file(self.revision)
        try:
            for self.doc in documents:
                extracts_sum.append(self.to_dict_sum())
                extracts_distinct_count.append(self.to_dict_distinct_count())
                extracts_min.append(self.to_dict_min())
                extracts_max.append(self.to_dict_max())
                extracts_fares_data_catalogue.append(
                    self.to_dict_fares_data_catalogue()
                )
                extracts_list.append(self.to_dict_list())
        except zipfile.BadZipFile as e:
            raise exceptions.FileError(filename=self.revision.upload_file.name) from e
        except exceptions.PipelineException:
            raise
        except Exception as e:
            raise exceptions.PipelineException from e

        for validation_dict in extracts_sum:
            if final_dictionary_sum:
                final_dictionary_sum = {
                    x: validation_dict.get(x, 0) + final_dictionary_sum.get(x, 0)
                    for x in set(final_dictionary_sum).union(validation_dict)
                }
            else:
                final_dictionary_sum = validation_dict.copy()

        for validation_dict in extracts_distinct_count:
            if final_dictionary_dictinct_count:
                final_dictionary_dictinct_count = {
                    x: validation_dict.get(x, 0).union(
                        final_dictionary_dictinct_count.get(x, 0)
                    )
                    for x in set(final_dictionary_dictinct_count).union(validation_dict)
                }
            else:
                final_dictionary_dictinct_count = validation_dict.copy()

        for key, value in final_dictionary_dictinct_count.items():
            final_dictionary_dictinct_count[key] = len(value)

        for validation_dict in extracts_min:
            if final_dictionary_min:
                final_dictionary_min = {
                    x: min(validation_dict.get(x, 0), final_dictionary_min.get(x, 0))
                    for x in set(final_dictionary_min).union(validation_dict)
                }
            else:
                final_dictionary_min = validation_dict.copy()

        for validation_dict in extracts_max:
            try:
                if final_dictionary_max:
                    final_dictionary_max = {
                        x: max(
                            validation_dict.get(x, 0),
                            final_dictionary_max.get(x, 0),
                        )
                        for x in set(final_dictionary_max).union(validation_dict)
                    }
                else:
                    final_dictionary_max = validation_dict.copy()
            except TypeError:
                for key in list(validation_dict.keys()):
                    final_dictionary_max[key] = None

        for validation_dict in extracts_list:
            if final_dictionary_list:
                final_dictionary_list = {
                    x: list(
                        set(validation_dict.get(x, 0) + final_dictionary_list.get(x, 0))
                    )
                    for x in set(final_dictionary_list).union(validation_dict)
                }
            else:
                final_dictionary_list = validation_dict.copy()
        for key, value in final_dictionary_list.items():
            final_dictionary_list[key] = sorted(value)

        final_extracts_dictionary = {
            **final_dictionary_sum,
            **final_dictionary_dictinct_count,
            **final_dictionary_min,
            **final_dictionary_max,
            **final_dictionary_list,
            **extracts_fares_data_catalogue[-1],
        }
        return final_extracts_dictionary

    def get_attr_for_dict(self, keys):
        try:
            data = {key: getattr(self, key) for key in keys}
        except ValueError as err:
            msg = "Unable to extract data from NeTEx file."
            raise ExtractionError(msg) from err

        return data

    def to_dict_min(self):
        keys = [
            "schema_version",
            "valid_from",
        ]
        return self.get_attr_for_dict(keys)

    def to_dict_max(self):
        keys = [
            "valid_to",
        ]
        return self.get_attr_for_dict(keys)

    def to_dict_list(self):
        keys = [
            "stop_point_refs",
        ]
        return self.get_attr_for_dict(keys)

    def to_dict_sum(self):
        keys = [
            "num_of_lines",
            "num_of_fare_zones",
            "num_of_sales_offer_packages",
            "num_of_fare_products",
        ]
        return self.get_attr_for_dict(keys)

    def to_dict_distinct_count(self):
        keys = [
            "num_of_user_profiles",
            "num_of_trip_products",
            "num_of_pass_products",
        ]
        return self.get_attr_for_dict(keys)

    def to_dict_fares_data_catalogue(self):
        keys = [
            "fares_data_catalogue",
        ]
        return self.get_attr_for_dict(keys)
