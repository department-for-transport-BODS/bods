from functools import cached_property
from logging import getLogger
from typing import Set, Tuple, Union
from datetime import date, timedelta
from itertools import chain
from django.conf import settings
from django.db import transaction, connection
from ddtrace import tracer

from transit_odp.otc.client.enums import RegistrationStatusEnum
from transit_odp.otc.models import (
    Licence,
    Operator,
    Service,
    InactiveService,
    LocalAuthority,
)

from transit_odp.otc.registry import Registry
from transit_odp.otc.populate_lta import PopulateLTA

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

    @tracer.wrap(service="otc_jobs", resource="get_missing_operators")
    def get_missing_operators(self) -> Set[int]:
        stored_ids = set(Operator.objects.values_list("operator_id", flat=True))
        new_ids = {service.operator.operator_id for service in self.registered_service}
        return new_ids - stored_ids

    @tracer.wrap(service="otc_jobs", resource="get_missing_licences")
    def get_missing_licences(self) -> Set[str]:
        stored_ids = set(Licence.objects.values_list("number", flat=True))
        new_ids = {service.licence.number for service in self.registered_service}
        return new_ids - stored_ids

    @tracer.wrap(service="otc_jobs", resource="get_missing_services")
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

    @tracer.wrap(service="otc_jobs", resource="load_licences")
    def load_licences(self):
        licences = []
        for licence_number in self.get_missing_licences():
            new_licence = self.registry.get_licence_by_number(licence_number)
            licences.append(Licence.from_registry_licence(new_licence))

        logger.info(f"loading {len(licences)} new licences into database")
        Licence.objects.bulk_create(licences)

    @tracer.wrap(service="otc_jobs", resource="load_operators")
    def load_operators(self):
        operators = []
        for op_id in self.get_missing_operators():
            new_operator = self.registry.get_operator_by_id(op_id)
            operators.append(Operator.from_registry_operator(new_operator))

        logger.info(f"loading {len(operators)} new operators into database")
        Operator.objects.bulk_create(operators)

    @tracer.wrap(service="otc_jobs", resource="load_services")
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

    @tracer.wrap(service="otc_jobs", resource="update_services_and_operators")
    def update_services_and_operators(self):
        all_services = Service.objects.select_related("operator", "licence").all()
        service_map = {
            (s.registration_number, s.service_type_description): s for s in all_services
        }
        entities_to_update = {
            "Licence": {"fields": set(), "items": []},
            "Operator": {"fields": set(), "items": []},
            "Service": {"fields": set(), "items": []},
        }

        for updated_service in self.registered_service:
            if updated_service.variation_number == 0:
                # This is a new service and wont need to be updated
                continue

            key = (
                updated_service.registration_number,
                updated_service.service_type_description,
            )
            db_service = service_map.get(key)

            if (
                db_service
                and db_service.variation_number < updated_service.variation_number
            ):
                # A change has been detected
                updated_service_kwargs = updated_service.dict()

                for db_item, kwargs, in (
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

    @tracer.wrap(service="otc_jobs", resource="load_inactive_services")
    def load_inactive_services(self, variation):

        InactiveService.objects.create(
            registration_number=variation.registration_number,
            registration_status=variation.registration_status,
            effective_date=variation.effective_date,
        )

    @tracer.wrap(service="otc_jobs", resource="delete_bad_data")
    def delete_bad_data(self):
        to_delete_services = self.registry.filter_by_status(
            *RegistrationStatusEnum.to_delete()
        )
        services = {
            service.registration_number
            for service in self.registry.get_services_with_past_effective_date(
                to_delete_services
            )
        }

        count, _ = Service.objects.filter(registration_number__in=services).delete()
        logger.info(f"{count} Services removed")

        count, _ = Licence.objects.filter(services=None).delete()
        logger.info(f"{count} Licences removed")
        count, _ = Operator.objects.filter(services=None).delete()
        logger.info(f"{count} Operators removed")

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
            effective_date__range=(days_ago, date.today())
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
            self.refresh_lta(_registrations)

    @tracer.wrap(service="otc_jobs", resource="refresh_lta")
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
                    f"Deleting LTA mapping for service ID: {_service_id} from the LTA relationship "
                )
        logger.info(
            f"Total count of registrations for refreshing LTAs is: {len(regs_to_update_lta)}"
        )
        refresh_lta = PopulateLTA()
        refresh_lta.refresh(regs_to_update_lta)
        logger.info(f"Completed updating the local authorities.")

    @tracer.wrap(service="otc_jobs", resource="_delete_all_otc_data")
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

    @cached_property
    def registered_service(self):
        return self.registry.filter_by_status(RegistrationStatusEnum.REGISTERED.value)
