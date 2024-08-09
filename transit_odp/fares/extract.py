import zipfile
from typing import List

from celery.utils.log import get_task_logger

from transit_odp.fares.netex import NeTExDocument, get_documents_from_zip
from transit_odp.pipelines import exceptions
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import FaresExtractedData

NeTExDocuments = List[NeTExDocument]

logger = get_task_logger(__name__)


class ExtractionError(Exception):
    """Generic exception for extraction errors."""

    code = "SYSTEM_ERROR"

    def __init__(self, message):
        self.message = message


class FaresDataCatalogueExtractor:
    def __init__(self, documents: NeTExDocuments):
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
        # self.documents = documents
        self.doc = NeTExDocuments
        self.file_obj = revision.upload_file

    def _attr_from_documents(self, attr):
        """Iterates over all documents and gets `attr`."""
        elements = getattr(self.doc, attr)
        return elements

    def _get_count(self, attr):
        """Gets the total counts of an `attr` in all documents."""
        return len(self._attr_from_documents(attr))

    def _get_user_type_count(self, attr):
        """Gets the total count of distinct UserType in all documents"""
        lists_user_types = self._attr_from_documents(attr)
        distinct_user_types = set(
            [value for sublist in lists_user_types for value in sublist]
        )
        return len(distinct_user_types)

    # @property
    # def schema_version(self):
    #     return min(doc.get_netex_version() for doc in self.documents)

    @property
    def schema_version(self):
        return float(self.doc.get_netex_version())

    @property
    def fare_zones(self):
        attr = "fare_zones"
        return self._attr_from_documents(attr)

    @property
    def sales_offer_packages(self):
        attr = "sales_offer_packages"
        return self._attr_from_documents(attr)

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
        return self._get_user_type_count(attr)

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
        trip_products_list = self.doc.get_number_of_trip_products()
        return trip_products_list

    @property
    def num_of_pass_products(self):
        pass_products_list = self.doc.get_number_of_pass_products()
        return pass_products_list

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
            national_operator_code_list = self.doc.get_multiple_attr_text_from_xpath(
                path
            )

            if national_operator_code_list:
                return national_operator_code_list
            return []
        except IndexError:
            return []

    @property
    def line_id(self):
        try:
            path = ["lines", "Line"]
            line_ids_list = self.doc.get_multiple_attr_ids_from_xpath(path)
            if line_ids_list:
                return list(dict.fromkeys(line_ids_list))
            return []
        except IndexError:
            return []

    @property
    def line_name(self):
        try:
            path = ["lines", "Line", "PublicCode"]
            line_name_list = self.doc.get_multiple_attr_text_from_xpath(path)
            if line_name_list:
                return list(dict.fromkeys(line_name_list))
            return []
        except IndexError:
            return []

    @property
    def tariff_basis(self):
        try:
            path = ["Tariff", "TariffBasis"]
            tariff_basis_list = self.doc.get_multiple_attr_text_from_xpath(path)
            if tariff_basis_list:
                return list(dict.fromkeys(tariff_basis_list))
            return []
        except IndexError:
            return []

    @property
    def product_type(self):
        try:
            path = ["fareProducts", "PreassignedFareProduct", "ProductType"]
            product_type_list = self.doc.get_multiple_attr_text_from_xpath(path)

            if product_type_list:
                return list(dict.fromkeys(product_type_list))
            return []
        except IndexError:
            return []

    @property
    def product_name(self):
        try:
            path = ["fareProducts", "PreassignedFareProduct", "Name"]
            product_name_list = self.doc.get_multiple_attr_text_from_xpath(path)

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
            user_type_list = self.doc.get_multiple_attr_text_from_xpath(path)

            if user_type_list:
                return list(dict.fromkeys(user_type_list))
            return []
        except IndexError:
            return []

    # @property
    # def fares_data_catalogue(self):
    #     fares_catalogue_extracted_data = []
    #     for doc in self.documents:
    #         fares_catalogue = FaresDataCatalogueExtractor(doc)
    #         fares_catalogue_extracted_data.append(fares_catalogue.to_dict())
    #     return fares_catalogue_extracted_data

    def extract(self) -> FaresExtractedData:
        """
        Processes a zip file.
        """
        extracts_sum = []
        extracts_min = []
        extracts_max = []
        extracts_list = []
        final_dictionary_sum = dict()
        final_dictionary_min = dict()
        final_dictionary_max = dict()
        final_dictionary_list = dict()

        if zipfile.is_zipfile(self.file_obj):
            logger.info(f"Extracting zip file {self.file_obj.name}")
            try:
                # with zipfile.ZipFile(self.file_obj.file, "r") as z:
                documents = get_documents_from_zip(self.file_obj)
                for self.doc in documents:
                    extracts_sum.append(self.to_dict_sum())
                    extracts_min.append(self.to_dict_min())
                    extracts_max.append(self.to_dict_max())
                    print("extracts_max>>> ", extracts_max)
                    extracts_list.append(self.to_dict_list())
            except zipfile.BadZipFile as e:
                raise exceptions.FileError(filename=self.file_obj.name) from e
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
            # print("final_dictionary_sum>>>> ", final_dictionary_sum)

            for validation_dict in extracts_min:
                if final_dictionary_min:
                    final_dictionary_min = {
                        x: min(
                            validation_dict.get(x, 0), final_dictionary_min.get(x, 0)
                        )
                        for x in set(final_dictionary_min).union(validation_dict)
                    }
                else:
                    final_dictionary_min = validation_dict.copy()
            # print("final_dictionary_min>>>> ", final_dictionary_min)

            # for validation_dict in extracts_max:
            #     if final_dictionary_max:
            #         final_dictionary_max = {x: max(validation_dict.get(x, 0), final_dictionary_max.get(x, 0))
            #             for x in set(final_dictionary_max).union(validation_dict)}
            #     else:
            #         final_dictionary_max = validation_dict.copy()
            # print("final_dictionary_max>>>> ", final_dictionary_max)

            for validation_dict in extracts_list:
                if final_dictionary_list:
                    final_dictionary_list = {
                        x: list(
                            set(
                                validation_dict.get(x, 0)
                                + final_dictionary_list.get(x, 0)
                            )
                        )
                        for x in set(final_dictionary_list).union(validation_dict)
                    }
                else:
                    final_dictionary_list = validation_dict.copy()
            # print("final_dictionary_list>>>> ", final_dictionary_list)

            final_final_dictionary = {
                **final_dictionary_sum,
                **final_dictionary_min,
                **final_dictionary_list,
            }
            print("final_final_dictionary>>> ", final_final_dictionary)
            return final_final_dictionary

    def to_dict_min(self):
        keys = [
            "schema_version",
            "valid_from",
        ]
        try:
            data = {key: getattr(self, key) for key in keys}
        except ValueError as err:
            msg = "Unable to extract data from NeTEx file."
            raise ExtractionError(msg) from err

        return data

    def to_dict_max(self):
        keys = [
            "valid_to",
        ]
        try:
            data = {key: getattr(self, key) for key in keys}
        except ValueError as err:
            msg = "Unable to extract data from NeTEx file."
            raise ExtractionError(msg) from err

        return data

    def to_dict_list(self):
        keys = [
            "stop_point_refs",
            "national_operator_code",
            "line_id",
            "line_name",
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

    def to_dict_sum(self):
        keys = [
            "num_of_lines",
            "num_of_fare_zones",
            "num_of_sales_offer_packages",
            "num_of_fare_products",
            "num_of_user_profiles",
            "num_of_trip_products",
            "num_of_pass_products",
        ]
        #         "schema_version",
        #         "num_of_lines",
        #         "num_of_fare_zones",
        #         "num_of_sales_offer_packages",
        #         "num_of_fare_products",
        #         "num_of_user_profiles",
        #         "num_of_trip_products",
        #         "num_of_pass_products",
        #         "valid_from",
        #         "valid_to",
        #         "stop_point_refs",
        # # keys = [
        #     "schema_version",
        #     "fare_zones",
        #     "sales_offer_packages",
        #     "fare_products",
        #     "user_profiles",
        #     "valid_from",
        #     "valid_to",
        #     "stop_point_refs",
        #     "national_operator_code",
        #     "line_id",
        #     "line_name",
        #     "tariff_basis",
        #     "product_type",
        #     "product_name"
        #     "user_type",
        # ]
        try:
            data = {key: getattr(self, key) for key in keys}
        except ValueError as err:
            msg = "Unable to extract data from NeTEx file."
            raise ExtractionError(msg) from err

        return data
