from logging import getLogger

from transit_odp.otc.weca.registry import Registry
from transit_odp.otc.models import Service

logger = getLogger(__name__)


class Loader:
    def __init__(self, registry: Registry):
        self.registry: Registry = registry

    def load(self):
        # sync all the records from
        logger.info("WECA job to refresh all the services started")
        self.registry.fetch_all_records()
        if len(self.registry.services) > 0:
            self.delete_services()
            self.load_services()

        logger.info("WECA job finished the execution")

    def load_services(self):
        services = self.registry.services
        logger.info("Loading services into the database")
        service_objects = []
        for service in services:
            service_objects.append(Service.from_registry_service(service, None, None))

        Service.objects.bulk_create(service_objects)
        logger.info("WECA services inserted into the database")

    def delete_services(self):
        Service.objects.filter(api_type="WECA").delete()
