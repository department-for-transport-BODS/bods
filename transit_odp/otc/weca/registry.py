from logging import getLogger
from typing import List

import numpy as np
import pandas as pd

from transit_odp.otc.models import Licence, Service
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
        """
        Make dataframe from the services pydentic model
        """
        services_list = [service.model_dump() for service in self.data]
        self.services = pd.DataFrame(services_list)

    def map_otc_licences(self) -> None:
        """
        Map the licences with the services, so that WECA services will have OTC_LICENCE link
        Unlike OTC, we will not create licences if they are missing in database table,
        We will leave licence_id field blank
        """
        licence_df = pd.DataFrame.from_records(Licence.objects.values("id", "number"))
        if not licence_df.empty:
            self.services = pd.merge(
                self.services,
                licence_df,
                left_on="licence",
                right_on="number",
                how="left",
            )
        self.services.rename(columns={"id_y": "licence_id"}, inplace=True)

    def get_missing_licences(self) -> None:
        """
        Returns the list of services with licences which are not present in
        """
        missing_licences = self.services[
            self.services["licence_id"].isnull()
        ].reset_index()["licence"]
        if not missing_licences.empty:
            return list(set(missing_licences.tolist()))
        return []

    def clean_services_list(self) -> None:
        """
        Drop un-necessary columns and rename others
        """
        self.services.drop(["id_x", "number"], inplace=True, axis=1)
        self.services.licence_id.replace({np.nan: None}, inplace=True)

    def process_services(self) -> None:
        """
        Fetch records from the weca api, and implement following
        1. Remove duplicate services and service name combination
        2. Merge the services based on service name seprated by pipe
        3. Ignore the services which belongs to OTC
        4. Map licence to the ones present in database
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
            logger.info("Map licences to database")
            self.map_otc_licences()
