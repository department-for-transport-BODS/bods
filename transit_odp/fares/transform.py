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
