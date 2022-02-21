from logging import getLogger
from typing import Set, Tuple, Union

from transit_odp.otc.models import Licence, Operator, Service
from transit_odp.otc.registry import Registry

logger = getLogger(__name__)


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
        new_ids = set(self.registry.operator_ids)
        return new_ids - stored_ids

    def get_missing_licences(self) -> Set[str]:
        stored_ids = set(Licence.objects.values_list("number", flat=True))
        new_ids = set(self.registry.licence_numbers)
        return new_ids - stored_ids

    def get_missing_services(self) -> Set[Tuple[str, str]]:
        stored_ids = set(
            Service.objects.values_list(
                "registration_number", "service_type_description"
            )
        )
        new_ids = set(self.registry.service_ids)
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
        all_services = Service.objects.select_related("operator", "licence").all()
        service_map = {
            (s.registration_number, s.service_type_description): s for s in all_services
        }
        entities_to_update = {
            "Licence": {"fields": set(), "items": []},
            "Operator": {"fields": set(), "items": []},
            "Service": {"fields": set(), "items": []},
        }

        for updated_service in self.registry.services:
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

    def load(self):
        self.load_licences()
        self.load_operators()
        self.load_services()
        self.update_services_and_operators()
