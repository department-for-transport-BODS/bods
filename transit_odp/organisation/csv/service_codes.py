import csv
import io
from typing import Set, Tuple

from transit_odp.organisation.models import TXCFileAttributes
from transit_odp.otc.models import Service as OTCService


class ServiceCodesCSV:
    REGISTERED = "Registered"
    MISSING_DATA = "Missing data"

    def __init__(self, organisation_id: int):
        self._organisation_id = organisation_id
        self.org_service_code_to_dataset = list(
            TXCFileAttributes.objects.filter(
                revision__dataset__organisation_id=organisation_id
            )
            .get_active_live_revisions()
            .select_related("revision__dataset")
            .values_list("service_code", "revision__dataset_id")
        )

    def get_queryset(self):
        return (
            OTCService.objects.get_all_in_organisation(self._organisation_id)
            .select_related("licence")
            .add_service_code()
            .order_by("licence__number", "service_code")
            .distinct("licence__number", "service_code")
        )

    def to_csv(self):
        string_ = io.StringIO()
        writer = csv.writer(string_, quoting=csv.QUOTE_ALL)
        writer.writerow(
            ("Service Status", "Licence Number", "Service Code", "Line", "Dataset ID")
        )

        for otc_service in self.get_queryset():
            row = self.get_row(otc_service)
            if row[0] == self.MISSING_DATA:
                writer.writerow(row)

        for otc_service in self.get_queryset():
            row = self.get_row(otc_service)
            if row[0] == self.REGISTERED:
                writer.writerow(row)

        string_.seek(0)
        return string_

    def get_row(self, otc_service: OTCService) -> Tuple:
        datasets: Set = {
            str(dataset_id)
            for service_code, dataset_id in self.org_service_code_to_dataset
            if service_code == otc_service.service_code
        }
        return (
            self.REGISTERED if len(datasets) > 0 else self.MISSING_DATA,
            otc_service.licence.number,
            otc_service.service_code,
            otc_service.service_number,
            ";".join(datasets),
        )
