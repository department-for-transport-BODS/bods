from typing import List

from transit_odp.naptan.models import StopPoint


class TransformationError(Exception):
    """Generic exception for extraction errors."""

    code = "SYSTEM_ERROR"

    def __init__(self, message):
        self.message = message


class NeTExDocumentsTransformer:
    def __init__(self, data: dict):
        self.data = data

    def transform_data(self):
        extracted_stops = self.data.pop("stop_point_refs")
        naptan_stop_ids = self.transform_stops(extracted_stops)
        self.data.update({"naptan_stop_ids": naptan_stop_ids})
        return self.data

    def transform_stops(self, extracted_stops: List):
        naptan_ids = set()
        atco_ids = set()

        for stop in extracted_stops:
            prefix, stop_code = stop.split(":")

            if stop_code:
                if prefix == "atco" or prefix == "naptan":
                    # atco_ids are prefixed by 'atco' or 'naptan' in the input XML
                    atco_ids.add(stop_code)
                else:
                    naptan_ids.add(stop_code)

        stop_points = list(
            StopPoint.objects.filter(naptan_code__in=naptan_ids).values_list(
                "atco_code", flat=True
            )
        )

        atco_ids.update(stop_points)

        naptan_stop_ids = list(
            StopPoint.objects.filter(atco_code__in=atco_ids).values_list(
                "id", flat=True
            )
        )

        return naptan_stop_ids

    def transform_fares_data_catalogue(self):
        # Remove duplication/sort code:
        # result_list = list(
        #     set([element for atco_area in scheduled_stop_points_list
        #     for element in atco_area])
        # )
        # result_list.sort()

        # Get all necessary data (atco area, etc.)
        # Save data as per each xml file
        transformed_netex = []
        extracted_file_name = self.data.pop("xml_file_name")
        extracted_product_type = self.data.pop("product_type")
        for file in extracted_file_name:
            transformed_netex.append(file)
            transformed_netex.append(extracted_product_type[0])


class FaresDataCatalogue:
    def __init__(self, data: dict, file, itr):
        self.data = data
        self.file = file
        print("self.data", self.data)
        self.file_itr = itr

    @property
    def xml_file_name(self):
        return self.file

    @property
    def valid_from(self):
        valid_from = self.data.get("fares_valid_from")
        return valid_from[self.file_itr]

    @property
    def valid_to(self):
        valid_to = self.data.get("fares_valid_to")
        return valid_to[self.file_itr]

    @property
    def national_operator_code(self):
        national_operator_code = self.data.get("national_operator_code")
        return national_operator_code[self.file_itr]

    @property
    def line_id(self):
        line_id = self.data.get("line_id")
        return line_id[self.file_itr]

    @property
    def line_name(self):
        line_name = self.data.get("line_name")
        return line_name[self.file_itr]

    @property
    def atco_area(self):
        atco_area = self.data.get("atco_area")
        return atco_area[self.file_itr]

    @property
    def tariff_basis(self):
        tariff_basis = self.data.get("tariff_basis")
        return tariff_basis[self.file_itr]

    @property
    def product_type(self):
        product_type = self.data.get("product_type")
        return product_type[self.file_itr]

    @property
    def product_name(self):
        product_name = self.data.get("product_name")
        return product_name[self.file_itr]

    @property
    def user_type(self):
        user_type = self.data.get("user_type")
        return user_type[self.file_itr]

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
            msg = "Unable to transform data from NeTEx file."
            raise TransformationError(msg) from err

        return data
