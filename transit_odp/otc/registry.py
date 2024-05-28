import logging
from datetime import date, datetime
from typing import List, Optional, Set, Tuple

from transit_odp.otc.client import OTCAPIClient
from transit_odp.otc.client.enums import RegistrationStatusEnum
from transit_odp.otc.dataclasses import Licence, Operator, Registration, Service
from transit_odp.otc.models import InactiveService

logger = logging.getLogger(__name__)


class RegistrationNumberNotFound(Exception):
    pass


class Registry:
    """
    Class that is responsible for transforming the OTC data.
    ie, dropping duplicate objects and normalising the data ready for batch loading
    into a database.

    Two typical usecases:

    First to completely sync with OTC registry. This typically take 3.5 hours.
    Currently used to completely refresh the data.

    registry = Registry()
    registry.sync_with_otc_registry()

    once this has run then the following properties will be populated
    registry.services -> all services that are in "Registered" status
    registry.operators -> all operators that have "Registered" services
    registry.licences -> all licences that "Registered" services against them

    Second to update from a given date. Will return services from a given date
    that are *either* "Registered" *or* services that are marked for deletion.

    registry = Registry()
    registry.get_variations_since(datetime(2022, 12, 25))
    note that registry.services will contain data that should be removed from the
    database. Use registry.filter_by_status("Registered") to get the services you want.
    """

    def __init__(self):
        self._operator_map = {}
        self._service_map = {}
        self._licence_map = {}
        self._client = OTCAPIClient()

    def sync_with_otc_registry(self) -> None:
        """
        helper method that runs what is required to completely sync the
        OTC database for use in BODS
        """
        self.add_all_latest_registered_variations()
        self.add_all_older_registered_variations()

    def add_all_latest_registered_variations(self) -> None:
        """
        Updates services with all registered variations that have the highest
        variation number
        """
        for registration in self._client.get_latest_variations_by_reg_status(
            RegistrationStatusEnum.REGISTERED.value
        ):
            self.update_registered_variations(registration)

        for delete_status in RegistrationStatusEnum.to_delete():
            for registration in self._client.get_latest_variations_by_reg_status(
                delete_status
            ):
                self.update_to_delete_variations(registration)

    def add_all_older_registered_variations(self) -> None:
        """
        Makes individual calls to API for each registration code that has previously
        returned a status in RegistrationStatusEnum.to_change(). Only status's in
        RegistrationStatusEnum.REGISTERED.value are kept.
        """
        further_lookups = self.get_further_lookup_ids()
        total = len(further_lookups)
        for current, registration_number in enumerate(further_lookups, start=1):
            logger.info(f"Requesting individual registration {current} of {total}")
            for variation in self.get_latest_variations_by_id(registration_number):
                if (
                    variation.registration_status
                    == RegistrationStatusEnum.REGISTERED.value
                ):
                    self.update_registered_variations(variation)

    def get_variations_since(self, when: datetime, services_to_check) -> List[Service]:
        """
        looks up all latest variations since a given date, any variations in the
        RegistrationStatusEnum.to_change() will be looked up again. This leaves
        registrations in RegistrationStatusEnum.REGISTERED and
        RegistrationStatusEnum.to_delete()
        RegistrationStatusEnum.to_change() with variation Zero
        """
        look_up_again = set()
        regs_to_update_lta = []
        registrations = []

        for reg in self._client.get_latest_variations_by_registration_code(
            services_to_check
        ):
            registrations.append(reg)

        for reg in self._client.get_latest_variations_since(when):
            if reg not in registrations:
                registrations.append(reg)
                regs_to_update_lta.append(reg)

        for registration in registrations:
            if registration.registration_status in RegistrationStatusEnum.to_change():
                if registration.variation_number != 0:
                    look_up_again.add(registration.registration_number)
                else:
                    self.update(registration)
            else:
                if (
                    registration.registration_status
                    == RegistrationStatusEnum.REGISTERED.value
                ):
                    self.update_registered_variations(registration)

                if (
                    registration.registration_status
                    in RegistrationStatusEnum.to_delete()
                ):
                    self.update(registration)

        for registration_number in look_up_again:
            older_variations = self.get_latest_variations_by_id(registration_number)
            for variation in older_variations:
                if (
                    variation.registration_status
                    == RegistrationStatusEnum.REGISTERED.value
                ):
                    self.update_registered_variations(variation)
                elif (
                    variation.registration_status in RegistrationStatusEnum.to_delete()
                ) or (
                    variation.registration_status in RegistrationStatusEnum.to_change()
                    and variation.variation_number == 0
                ):
                    self.update(variation)

        return regs_to_update_lta

    def filter_by_status(self, *args) -> List[Service]:
        return [
            service for service in self.services if service.registration_status in args
        ]

    def get_services_with_past_effective_date(
        self, to_delete_services
    ) -> List[Service]:
        service_list = []
        for service in to_delete_services:
            if service.effective_date:
                if service.effective_date <= date.today():
                    service_list.append(service)
            else:
                service_list.append(service)
        return service_list

    def get_services_with_future_effective_date(self, services) -> List[Service]:
        """
        Gets a list of the all services whoes status are in RegistrationStatusEnum.to_delete().
        and their effecitve date is in future
        """
        service_list = [
            service
            for service in services
            if (service.effective_date and service.effective_date > date.today())
        ]

        return service_list

    def get_latest_variations_by_id(self, registration_number) -> List[Registration]:
        """
        Gets a list of the all variations by registration number that are ordered by
        variation number descending. We then return all the entries with the highest
        variation number whose status are not in RegistrationStatusEnum.to_change().
        then we will check if the variation number 0 is with status RegistrationStatusEnum.to_change()
        Return that variation because we have to remove that from database,
        Else we return an empty list
        """
        registrations = self._client.get_variations_by_registration_code_desc(
            registration_number
        )
        for registration in registrations:
            if (
                registration.registration_status
                not in RegistrationStatusEnum.to_change()
            ) or (
                registration.variation_number == 0
                and registration.registration_status
                in RegistrationStatusEnum.to_change()
            ):
                highest_variation_number = registration.variation_number
                return [
                    variation
                    for variation in registrations
                    if variation.variation_number == highest_variation_number
                ]
        return []

    def get_further_lookup_ids(self) -> Set[str]:
        """
        Returns a set of all registration numbers whos latest variation is in
        RegistrationStatusEnum.to_change(), we do this so we can look them up again
        and get the latest registered
        """
        lookup_ids = set()
        for status in RegistrationStatusEnum.to_change():
            for registration in self._client.get_latest_variations_by_reg_status(
                status
            ):
                lookup_ids.add(registration.registration_number)

        return lookup_ids

    def update_registered_variations(self, variation: Registration) -> None:
        if variation.variation_number == 0:
            if variation.effective_date:
                if variation.effective_date <= date.today():
                    self.update(variation)
                else:
                    defaults = {
                        "registration_status": variation.registration_status,
                        "effective_date": variation.effective_date,
                    }
                    InactiveService.objects.update_or_create(
                        registration_number=variation.registration_number,
                        defaults=defaults,
                    )
            else:
                self.update(variation)
        else:
            self.update(variation)

    def update_to_delete_variations(self, variation: Registration) -> None:
        if variation.effective_date:
            if variation.effective_date > date.today():
                self.update(variation)

    def update(self, registration: Registration) -> None:
        """
        Performs normalisation and drops duplicates, will keep highest variation
        """
        licence_number = registration.licence_number
        registration_number = registration.registration_number
        service_type_description = registration.service_type_description
        operator_id = registration.operator_id

        service = self._service_map.get((registration_number, service_type_description))
        if service and registration.variation_number < service.variation_number:
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
