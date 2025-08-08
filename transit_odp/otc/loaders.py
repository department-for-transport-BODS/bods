import pandas as pd
from datetime import date, datetime, timedelta
from functools import cached_property
from itertools import chain
from logging import getLogger
from typing import List, Set, Tuple, Union

from django.conf import settings
from django.db import transaction

from transit_odp.otc.client.enums import RegistrationStatusEnum
from transit_odp.otc.models import (
    InactiveService,
    Licence,
    LocalAuthority,
    Operator,
    Service,
)
from transit_odp.otc.populate_lta import PopulateLTA
from transit_odp.otc.registry import Registry
from transit_odp.otc.utils import get_dataframe, find_differing_registration_numbers
from transit_odp.otc.constants import API_TYPE_EP

logger = getLogger(__name__)


class LoadFailedException(Exception):
    pass


class Loader:
    def __init__(self, registry: Registry):
        self.registry: Registry = registry

    def _update_item(self, db_item: Union[Service, Licence, Operator], new_item: dict):
        changed_fields = []
        for attr, value in new_item.items():
            db_value = getattr(db_item, attr)
            if db_value != value:
                setattr(db_item, attr, value)
                changed_fields.append(attr)

        return db_item, set(changed_fields)

    def get_missing_operators(self) -> Set[int]:
        stored_ids = set(Operator.objects.values_list("operator_id", flat=True))
        new_ids = {service.operator.operator_id for service in self.registered_service}
        return new_ids - stored_ids

    def get_missing_licences(self) -> Set[str]:
        stored_ids = set(Licence.objects.values_list("number", flat=True))
        new_ids = {service.licence.number for service in self.registered_service}
        return new_ids - stored_ids

    def get_missing_services(self) -> Set[Tuple[str, str]]:
        stored_ids = set(
            Service.objects.values_list(
                "registration_number", "service_type_description"
            )
        )
        new_ids = {
            (service.registration_number, service.service_type_description)
            for service in self.registered_service
        }
        return new_ids - stored_ids

    def load_licences(self):
        licences = []
        for licence_number in self.get_missing_licences():
            new_licence = self.registry.get_licence_by_number(licence_number)
            licences.append(Licence.from_registry_licence(new_licence))

        logger.info(f"loading {len(licences)} new licences into database")
        Licence.objects.bulk_create(licences)

    def load_operators(self):
        operators = []
        for op_id in self.get_missing_operators():
            new_operator = self.registry.get_operator_by_id(op_id)
            operators.append(Operator.from_registry_operator(new_operator))

        logger.info(f"loading {len(operators)} new operators into database")
        Operator.objects.bulk_create(operators)

    def load_services(self):
        operator_map = {op.operator_id: op for op in Operator.objects.all()}
        licence_map = {lic.number: lic for lic in Licence.objects.all()}
        services = []

        for key in self.get_missing_services():
            service = self.registry.get_service_by_key(*key)
            operator = operator_map[service.operator.operator_id]
            licence = licence_map[service.licence.number]

            services.append(Service.from_registry_service(service, operator, licence))

        logger.info(f"loading {len(services)} new services into database")
        Service.objects.bulk_create(services)

    def update_services_and_operators(self):
        all_services = Service.objects.select_related("operator", "licence").filter(
            api_type__isnull=True
        )
        service_map = {
            (s.registration_number, s.service_type_description): s for s in all_services
        }
        entities_to_update = {
            "Licence": {"fields": set(), "items": []},
            "Operator": {"fields": set(), "items": []},
            "Service": {"fields": set(), "items": []},
        }

        possible_services_to_update = self.registered_service + self.to_delete_service
        for updated_service in possible_services_to_update:
            key = (
                updated_service.registration_number,
                updated_service.service_type_description,
            )
            db_service = service_map.get(key)
            if (
                db_service
                and updated_service.variation_number == 0
                and db_service.last_modified >= updated_service.last_modified
            ):
                # This is a new service and wont need to be updated
                continue

            if db_service and (
                db_service.variation_number < updated_service.variation_number
                or db_service.variation_number == 0
            ):
                # A change has been detected
                updated_service_kwargs = updated_service.dict()

                for (db_item, kwargs,) in (
                    (db_service.licence, updated_service_kwargs.pop("licence")),
                    (db_service.operator, updated_service_kwargs.pop("operator")),
                    (db_service, updated_service_kwargs),
                ):
                    # group the changed entities along with which fields have changed
                    # for use in bulk_update, this is to avoid hitting the database
                    # with every field
                    updated_entity, updated_fields = self._update_item(db_item, kwargs)
                    if updated_fields:
                        key = updated_entity.__class__.__name__
                        fields = entities_to_update[key]["fields"]
                        entities_to_update[key]["fields"] = fields.union(updated_fields)
                        entities_to_update[key]["items"].append(updated_entity)

        for Model in (Licence, Operator, Service):
            key = Model.__name__
            if entities_to_update[key]["items"]:
                Model.objects.bulk_update(
                    entities_to_update[key]["items"], entities_to_update[key]["fields"]
                )
            logger.info(f'Updated {len(entities_to_update[key]["items"])} {key}')

    def update_all_services_and_operators(self):
        """
        To update all the services which have been found without any conditional check,
        This method is duplicate of update services and operators method with only difference of conditions,
        Kept it seprate in order to isolate the change for the job
        """
        all_services = Service.objects.select_related("operator", "licence").filter(
            api_type__isnull=True
        )
        service_map = {
            (s.registration_number, s.service_type_description): s for s in all_services
        }
        entities_to_update = {
            "Licence": {"fields": set(), "items": []},
            "Operator": {"fields": set(), "items": []},
            "Service": {"fields": set(), "items": []},
        }

        possible_services_to_update = self.registered_service + self.to_delete_service
        for updated_service in possible_services_to_update:
            key = (
                updated_service.registration_number,
                updated_service.service_type_description,
            )
            db_service = service_map.get(key)
            if (
                db_service
                and updated_service.variation_number == 0
                and db_service.last_modified > updated_service.last_modified
            ):
                # This is a new service and wont need to be updated
                continue
            
            if not db_service:
                logger.info("Unable to find the service in database {}".format(key))
                continue

            # A change has been detected
            updated_service_kwargs = updated_service.dict()

            for (db_item, kwargs,) in (
                (db_service.licence, updated_service_kwargs.pop("licence")),
                (db_service.operator, updated_service_kwargs.pop("operator")),
                (db_service, updated_service_kwargs),
            ):
                # group the changed entities along with which fields have changed
                # for use in bulk_update, this is to avoid hitting the database
                # with every field
                updated_entity, updated_fields = self._update_item(db_item, kwargs)
                if updated_fields:
                    key = updated_entity.__class__.__name__
                    fields = entities_to_update[key]["fields"]
                    entities_to_update[key]["fields"] = fields.union(updated_fields)
                    entities_to_update[key]["items"].append(updated_entity)

        for Model in (Licence, Operator, Service):
            key = Model.__name__
            if entities_to_update[key]["items"]:
                Model.objects.bulk_update(
                    entities_to_update[key]["items"], entities_to_update[key]["fields"]
                )
            logger.info(f'Updated {len(entities_to_update[key]["items"])} {key}')

    def load_inactive_services(self, variation):
        InactiveService.objects.create(
            registration_number=variation.registration_number,
            registration_status=variation.registration_status,
            effective_date=variation.effective_date,
        )

    def delete_bad_data(self):
        to_delete_services = self.to_delete_service
        services = set(
            [
                service.registration_number
                for service in self.registry.get_services_with_past_effective_date(
                    to_delete_services
                )
            ]
            + [
                service.registration_number
                for service in self.to_change_services_with_variation_zero
            ]
        )

        count, _ = Service.objects.filter(registration_number__in=services).delete()
        logger.info(f"{count} Services removed because of effective date in past")

        count, _ = Licence.objects.filter(services=None).delete()
        logger.info(f"{count} Licences removed")
        count, _ = Operator.objects.filter(services=None).delete()
        logger.info(f"{count} Operators removed")

    def inactivate_bad_services(self):
        """
        Inactivate all services whoes status are in RegistrationStatusEnum.to_delete().
        and their effecitve date is in future
        """
        services = self.registry.get_services_with_future_effective_date(
            services=self.to_delete_service
        )

        for service in services:
            defaults = {
                "registration_status": service.registration_status,
                "effective_date": service.effective_date,
            }
            InactiveService.objects.update_or_create(
                registration_number=service.registration_number, defaults=defaults
            )
        logger.info(
            f"{len(services)} Services inactivated because of effective date in future"
        )

    def load(self):
        """
        The method is used to update the database, add and remove unnecessary objects.
        """
        days_ago = date.today() - timedelta(
            days=settings.OTC_DAILY_JOB_EFFECTIVE_DATE_TIMEDELTA
        )
        most_recently_modified = (
            Service.objects.filter(last_modified__isnull=False)
            .order_by("last_modified")
            .last()
        )
        service_with_valid_effective_date = Service.objects.filter(
            effective_date__range=(days_ago, date.today()), api_type__isnull=True
        ).values_list("registration_number", flat=True)
        inactive_service_with_valid_effective_date = InactiveService.objects.filter(
            effective_date__range=(days_ago, date.today())
        ).values_list("registration_number", flat=True)
        services_to_check = list(
            set(
                chain(
                    service_with_valid_effective_date,
                    inactive_service_with_valid_effective_date,
                )
            )
        )

        if (
            most_recently_modified is None
            or most_recently_modified.last_modified is None
        ):
            logger.error("Cant find last modified date in database, giving up")
            raise LoadFailedException("Cannot calculate last run date of task")

        with transaction.atomic():
            _registrations = self.registry.get_variations_since(
                most_recently_modified.last_modified, services_to_check
            )

            self.load_licences()
            self.load_operators()
            self.load_services()
            self.update_services_and_operators()
            self.delete_bad_data()
            self.inactivate_bad_services()
            self.refresh_lta(_registrations)

    def refresh_lta(self, regs_to_update_lta):
        for registration in regs_to_update_lta:
            _service = Service.objects.filter(
                registration_number=registration.registration_number
            ).values_list("id")
            if _service:
                _service_id = _service[0][0]
                _ = LocalAuthority.registration_numbers.through.objects.filter(
                    service_id=_service_id
                ).delete()
                logger.info(
                    f"Deleting LTA mapping for service ID: {_service_id} \
                    from the LTA relationship"
                )
        logger.info(
            f"Total count of registrations for refreshing \
            LTAs is: {len(regs_to_update_lta)}"
        )
        refresh_lta = PopulateLTA()
        refresh_lta.refresh(regs_to_update_lta)
        logger.info("Completed updating the local authorities.")

    def _delete_all_otc_data(self) -> None:
        logger.info("Clearing OTC tables")
        count, _ = Service.objects.all().delete()
        logger.info(f"Deleted {count} OTC Services")
        count, _ = Licence.objects.all().delete()
        logger.info(f"Deleted {count} OTC Licences")
        count, _ = Operator.objects.all().delete()
        logger.info(f"Deleted {count} OTC Operators")

    @transaction.atomic
    def load_into_fresh_database(self):
        new_otc_objects = []
        self.registry.sync_with_otc_registry()
        self._delete_all_otc_data()

        for licence in self.registry.licences:
            new_otc_objects.append(Licence.from_registry_licence(licence))

        logger.info(
            f"loading {len(new_otc_objects)} new licences into database from API"
        )
        Licence.objects.bulk_create(new_otc_objects)

        new_otc_objects = []
        for operator in self.registry.operators:
            new_otc_objects.append(Operator.from_registry_operator(operator))

        logger.info(
            f"loading {len(new_otc_objects)} new operators into database from API"
        )
        Operator.objects.bulk_create(new_otc_objects)

        new_otc_objects = []
        operator_map = {op.operator_id: op for op in Operator.objects.all()}
        licence_map = {lic.number: lic for lic in Licence.objects.all()}
        for service in self.registry.services:
            operator = operator_map[service.operator.operator_id]
            licence = licence_map[service.licence.number]
            new_otc_objects.append(
                Service.from_registry_service(service, operator, licence)
            )

        logger.info(
            f"loading {len(new_otc_objects)} new services into database from API"
        )
        Service.objects.bulk_create(new_otc_objects)

        self.inactivate_bad_services()

    @cached_property
    def registered_service(self):
        return self.registry.filter_by_status(RegistrationStatusEnum.REGISTERED.value)

    @cached_property
    def to_change_services_with_variation_zero(self) -> List[Service]:
        """Property to get list of variations which are in RegistrationStatusEnum.to_change
        with the variation number Zero

        Returns:
            List[Service]: List of services
        """
        return [
            service
            for service in self.registry.services
            if service.registration_status in RegistrationStatusEnum.to_change()
            and service.variation_number == 0
        ]

    @cached_property
    def to_delete_service(self):
        return self.registry.filter_by_status(*RegistrationStatusEnum.to_delete())

    def load_given_services(self, services: str):
        if services == "":
            logger.info("No Services passed, Skipping the job")
            return
        services_list = services.split(",")
        logger.info(f"Job will be executed for following services {services_list}")

        with transaction.atomic():
            _registrations = self.registry.get_variations_since(
                datetime.today(), services_list
            )

            services_without_localauthority = []
            for service in _registrations:
                if service.local_authorities is None:
                    logger.info(f"Found service without localauthority {service}")
                    services_without_localauthority.append(service.registration_number)

            if len(services_without_localauthority):
                logger.info(
                    f"Following services does not have localauthortiy {list(set(services_without_localauthority))}"
                )

            self.load_licences()
            self.load_operators()
            self.load_services()
            self.update_all_services_and_operators()
            self.delete_bad_data()
            self.inactivate_bad_services()
            self.refresh_lta(_registrations)

    def load_services_with_updated_service_numbers(self):
        """
        Loads all services where service numbers have been updated with enhanced error handling.
        """
        logger.info("Starting celery task to check for updates on otc...")
        columns = [
            "registration_number",
            "variation_number",
            "service_number",
            "registration_status",
        ]

        try:
            all_services_bods_db = Service.objects.exclude(
                api_type=API_TYPE_EP
            ).values()
            if not all_services_bods_db:
                logger.warning("No services found in the database.")
                return

            all_services_bods_df = pd.DataFrame.from_records(all_services_bods_db)
            if all_services_bods_df.empty:
                logger.warning("Empty DataFrame created from database services.")
                return

            all_services_bods_df = all_services_bods_df[columns]
            new_otc_objects = []

            logger.info("Running sync with otc_registry...")
            try:
                self.registry.sync_with_otc_registry()
            except Exception as e:
                logger.error(f"Failed to sync with otc_registry: {str(e)}")
                raise Exception(f"OTC registry sync failed: {str(e)}") from e

            for service in self.registry.services:
                new_otc_objects.append(service)

            if not new_otc_objects:
                logger.warning("No services retrieved from otc_registry.")
                return

            logger.info("Completed sync with otc_registry.")

            otc_objects_df = get_dataframe(new_otc_objects, columns)
            if otc_objects_df.empty:
                logger.warning("Empty DataFrame created from OTC registry services.")
                return

            registration_numbers = find_differing_registration_numbers(
                all_services_bods_df, otc_objects_df
            )
            if not registration_numbers:
                logger.info("No differing registration numbers found.")
                return

            registration_numbers_to_update = ",".join(registration_numbers)
            if not registration_numbers_to_update:
                logger.warning(
                    "No registration numbers to update after join operation."
                )
                return

            logger.info("Running refresh job for list of services...")

            try:
                registry = Registry()
                loader = Loader(registry)
                loader.load_given_services(registration_numbers_to_update)
            except ValueError as ve:
                logger.error(f"Invalid input for service loader: {str(ve)}")
                raise Exception(
                    f"Invalid input error in task_refresh_otc_services with input: {registration_numbers_to_update}. Error: {str(ve)}"
                ) from ve
            except ConnectionError as ce:
                logger.error(f"Connection error during service loading: {str(ce)}")
                raise Exception(
                    f"Connection error in task_refresh_otc_services with input: {registration_numbers_to_update}. Error: {str(ce)}"
                ) from ce
            except Exception as e:
                logger.error(f"Unexpected error during service loading: {str(e)}")
                raise Exception(
                    f"Unexpected error in task_refresh_otc_services with input: {registration_numbers_to_update}. Error: {str(e)}"
                ) from e

            logger.info("Finished refresh job for list of services.")

        except Exception as e:

            logger.error(
                f"Critical error in load_services_with_updated_service_numbers: {str(e)}"
            )
            raise Exception(
                f"Critical error in service update process: {str(e)}"
            ) from e
