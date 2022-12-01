import logging
from datetime import datetime
from typing import List, Optional, Tuple

from transit_odp.otc.client import OTCAPIClient
from transit_odp.otc.client.enums import RegistrationStatusEnum
from transit_odp.otc.dataclasses import Licence, Operator, Registration, Service

logger = logging.getLogger(__name__)


class RegistrationNumberNotFound(Exception):
    pass


class Registry:
    """
    Class that is responsible for transforming the OTC data.
    ie, dropping duplicate objects and normalising the data ready for batch loading
    into a database
    """

    def __init__(self):
        self._operator_map = {}
        self._service_map = {}
        self._licence_map = {}
        self._client = OTCAPIClient()

    def add_all_latest_registered_variations(self) -> None:
        """
        Updates services with all registered variations that have the highest
        variation number
        """
        for registration in self._client.get_latest_variations_by_reg_status(
            RegistrationStatusEnum.REGISTERED.value
        ):
            self.update(registration)

    def add_all_older_registered_variations(self) -> None:
        further_lookups = self.get_further_lookup_ids()
        total = len(further_lookups)
        for current, registration_number in enumerate(further_lookups, start=1):
            logger.info(f"Requesting individual registration {current} of {total}")
            for variation in self.get_latest_variations_by_id(registration_number):
                if (
                    variation.registration_status
                    == RegistrationStatusEnum.REGISTERED.value
                ):
                    self.update(variation)

    def get_variations_since(self, when: datetime) -> List[Service]:
        for registration in self._client.get_latest_variations_since(when):
            if registration.registration_status in RegistrationStatusEnum.to_change():
                older_variations = self.get_latest_variations_by_id(
                    registration.registration_number
                )
                for variation in older_variations:
                    self.update(variation)
            else:
                self.update(registration)

        return list(self._service_map.values())

    def filter_by_status(self, *args):
        return [
            service for service in self.services if service.registration_status in args
        ]

    def get_latest_variations_by_id(self, registration_number) -> List[Registration]:
        registrations = self._client.get_variations_by_registration_code_desc(
            registration_number
        )
        for registration in registrations:
            if (
                registration.registration_status
                not in RegistrationStatusEnum.to_change()
            ):
                highest_variation_number = registration.variation_number
                return [
                    variation
                    for variation in registrations
                    if variation.variation_number == highest_variation_number
                ]
        return []

    def get_further_lookup_ids(self):
        lookup_ids = set()
        for status in RegistrationStatusEnum.to_change():
            for registration in self._client.get_latest_variations_by_reg_status(
                status
            ):
                lookup_ids.add(registration.registration_number)

        return lookup_ids

    def update(self, registration: Registration):
        licence_number = registration.licence_number
        registration_number = registration.registration_number
        service_type_description = registration.service_type_description
        operator_id = registration.operator_id

        if (registration_number, service_type_description) in self._service_map:
            return

        if licence_number not in self._licence_map:
            licence = Licence(**registration.dict())
            self._licence_map[licence_number] = licence
        else:
            licence = self._licence_map[licence_number]

        if operator_id not in self._operator_map:
            operator = Operator(**registration.dict())
            self._operator_map[operator_id] = operator
        else:
            operator = self._operator_map[operator_id]

        self._service_map[(registration_number, service_type_description)] = Service(
            operator=operator, licence=licence, **registration.dict()
        )

    @property
    def operators(self) -> List[Operator]:
        return list(self._operator_map.values())

    @property
    def operator_ids(self) -> List[int]:
        return list(self._operator_map.keys())

    def get_operator_by_id(self, id_: int) -> Optional[Operator]:
        return self._operator_map.get(id_)

    @property
    def services(self) -> List[Service]:
        return list(self._service_map.values())

    @property
    def service_ids(self) -> List[Tuple[str, str]]:
        return list(self._service_map.keys())

    def get_service_by_key(
        self, registration_number, service_type_description
    ) -> Optional[Service]:
        return self._service_map.get((registration_number, service_type_description))

    @property
    def licences(self) -> List[Licence]:
        return list(self._licence_map.values())

    @property
    def licence_numbers(self) -> List[str]:
        return list(self._licence_map.keys())

    def get_licence_by_number(self, licence_number: str) -> Optional[Licence]:
        return self._licence_map.get(licence_number)
