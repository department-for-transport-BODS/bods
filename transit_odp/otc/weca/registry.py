from logging import getLogger

import pandas as pd

from transit_odp.otc.models import Service
from transit_odp.otc.weca.client import APIResponse, WecaClient

logger = getLogger(__name__)


class Registry:
    def __init__(self) -> None:
        self._client = WecaClient()
        self.services = pd.DataFrame()
        self.data = []
        self.fields = []

    def fetch_all_records(self) -> APIResponse:
        """
        Fetch the records from the weca service
        """
        logger.info("Fetching WECA services")
        response = self._client.fetch_weca_services()
        self.data = response.data
        self.fields = response.fields
        logger.info("Total Services found {}".format(len(self.data)))
        return response

    def remove_duplicates(self) -> None:
        """
        Remove all the duplicate registration_number and service_number combination
        """
        self.services = self.services.drop_duplicates(
            ["registration_number", "service_number"], keep="first"
        )

    def merge_service_numbers(self) -> None:
        """
        There can be same registration number with multiple service numbers,
        Method will merge the rows with service numbers seprated by pipe |
        """
        aggregation = {
            col: "first" if col != "service_number" else "|".join
            for col in self.services.columns
        }
        self.services = self.services.groupby(
            "registration_number", as_index=False
        ).agg(aggregation)

    def ignore_otc_services(self) -> None:
        """
        To ignore the services which belongs to OTC but are comming in WECA API
        Expectation is such scenarios will not happen but if they are those will be
        skipped from the dataframe
        """
        services_queryset = Service.objects.filter(
            registration_number__in=self.services["registration_number"].tolist(),
            api_type__isnull=True,
        ).values_list("registration_number")
        services_to_ignore = [service[0] for service in services_queryset]
        logger.info(
            "Found {} services of OTC in weca data, and these will be ignored".format(
                len(services_to_ignore)
            )
        )
        self.services = self.services[
            ~self.services["registration_number"].isin(services_to_ignore)
        ]

    def convert_services_to_df(self) -> None:
        services_list = [service.model_dump() for service in self.data]
        self.services = pd.DataFrame(services_list)

    def process_services(self) -> None:
        """
        Fetch records from the weca api, and implement following
        1. Remove duplicate services and service name combination
        2. Merge the services based on service name seprated by pipe
        3. Ignore the services which belongs to OTC
        """
        self.fetch_all_records()
        self.convert_services_to_df()
        if not self.services.empty:
            logger.info("Removing WECA duplicates.")
            self.remove_duplicates()
            logger.info(
                "Merging WECA records for same registration numbers by making service name seprated from pipe."
            )
            self.merge_service_numbers()
            logger.info("Ignoring OTC services present in WECA records.")
            self.ignore_otc_services()
