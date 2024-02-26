from logging import getLogger

from transit_odp.otc.models import Service
from transit_odp.otc.weca.registry import Registry

logger = getLogger(__name__)


class Loader:
    def __init__(self, registry: Registry):
        self.registry: Registry = registry

    def load(self):
        # sync all the records from
        logger.info("WECA job to refresh all the services started")
        self.registry.process_services()
        if len(self.registry.services) > 0:
            self.delete_services()
            self.load_services()

        logger.info("WECA job finished the execution")

    def load_services(self):
        logger.info("Loading services into the database")
        service_objects = []
        self.registry.services.reset_index()
        for index, service in self.registry.services.iterrows():
            service_objects.append(Service(**service))

        Service.objects.bulk_create(service_objects)
        logger.info("WECA services inserted into the database")

    def delete_services(self):
        Service.objects.filter(api_type="WECA").delete()
