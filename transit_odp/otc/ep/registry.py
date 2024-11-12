from logging import getLogger

import numpy as np
import pandas as pd

from transit_odp.otc.models import Licence, Service, Operator
from transit_odp.otc.ep.client import APIResponse, EPClient

logger = getLogger(__name__)


class Registry:
    def __init__(self) -> None:
        self._client = EPClient()
        self.services = pd.DataFrame()
        self.data = []

    def fetch_all_records(self) -> APIResponse:
        """
        Fetch the records from the EP service
        """
        logger.info("Fetching EP services")
        response = self._client.fetch_ep_services()
        self.data = response.Results
        logger.info("Total Services found {}".format(len(self.data)))
        return response

    def remove_duplicates(self) -> None:
        """
        Remove all the duplicate registration_number and service_number combination
        """
        self.services = self.services.drop_duplicates(
            ["registration_number", "service_number"], keep="first"
        )

    def ignore_existing_services(self) -> None:
        """
        To ignore the existing services which belongs to OTC but are comming in EP API
        Expectation is such scenarios will not happen but if they are those will be
        skipped from the dataframe
        """
        services_df = pd.DataFrame.from_records(
            Service.objects.filter(
                registration_number__in=self.services["registration_number"].tolist(),
                api_type__isnull=True,
            ).values_list("registration_number", "service_number"),
            columns=["registration_number", "service_number"],
        )

        services_df["service_number"] = services_df["service_number"].apply(
            lambda x: str(x).split("|")
        )
        services_df = services_df.explode("service_number")
        services_df.drop_duplicates(inplace=True)
        self.services = self.services.merge(
            services_df,
            on=["registration_number", "service_number"],
            how="left",
            indicator=True,
        )

        logger.info(
            "Found {} services of OTC in EP data, and these will be ignored".format(
                len(self.services[self.services["_merge"] == "both"])
            )
        )
        logger.info(
            "Found following services of OTC in EP data, and these were be ignored {}".format(
                self.services[self.services["_merge"] == "both"]
            )
        )
        self.services = self.services[self.services["_merge"] == "left_only"].drop(
            columns=["_merge"]
        )

    def convert_services_to_df(self) -> None:
        """
        Make dataframe from the services pydentic model
        """
        services_list = [service.model_dump() for service in self.data]
        self.services = pd.DataFrame(services_list)

    def map_licences(self) -> None:
        """
        Map the licences with the services, so that EP services will have OTC_LICENCE link
        Unlike OTC, we will not create licences if they are missing in database table,
        We will leave licence_id field blank
        """
        licence_df = pd.DataFrame.from_records(Licence.objects.values("id", "number"))
        licence_df.rename(columns={"id": "licence_id"}, inplace=True)
        if not licence_df.empty:
            self.services = pd.merge(
                self.services,
                licence_df,
                left_on="licence",
                right_on="number",
                how="left",
            )
            self.services.licence_id.replace({np.nan: None}, inplace=True)
        else:
            self.services["licence_id"] = None

    def map_operatorname(self) -> None:
        """
        Map the Operator name with the services, so that EP services will have OTC_Operator link
        We will not create Operators if they are missing in database table,
        We will leave operator_id field blank
        """
        operator_df = pd.DataFrame.from_records(
            Operator.objects.values("id", "operator_name")
        )
        operator_df.rename(columns={"id": "operator_id"}, inplace=True)
        if not operator_df.empty:
            self.services = pd.merge(
                self.services,
                operator_df,
                left_on="operator_name",
                right_on="operator_name",
                how="left",
            )
            self.services.operator_id.replace({np.nan: None}, inplace=True)
        else:
            self.services["operator_id"] = None

    def get_missing_licences(self) -> None:
        """
        Returns the list of services with licences which
        are not present in database
        """
        if not self.services.empty:
            missing_licences = self.services[
                self.services["licence_id"].isnull()
            ].reset_index()["licence"]
            return list(set(missing_licences.tolist()))
        return []

    def remove_columns(self):
        """
        This function removes the column operator_name and number from the services dataframe
        """
        columns_to_remove = ["operator_name", "number"]
        if not self.services.empty:
            for column in columns_to_remove:
                if column in self.services.columns:
                    self.services.drop([column], axis=1, inplace=True)

    def process_services(self) -> None:
        """
        Fetch records from the EP api, and implement following
        1. Remove duplicate services and service name combination
        2. Merge the services based on service name seprated by pipe
        3. Ignore the services which belongs to OTC and WECA
        4. Map licence to the ones present in database
        """
        self.fetch_all_records()
        self.convert_services_to_df()
        if not self.services.empty:
            logger.info("Removing EP duplicates.")
            self.remove_duplicates()
            logger.info(
                "Merging EP records for same registration numbers by making service name seprated from pipe."
            )
            logger.info("Ignoring OTC services present in EP records.")
            self.ignore_existing_services()
            logger.info("Map licences to database")
            self.map_licences()
            logger.info("Map operator name to database")
            self.map_operatorname()
            self.remove_columns()
