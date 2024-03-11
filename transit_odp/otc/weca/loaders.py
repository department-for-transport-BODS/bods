from logging import getLogger

from transit_odp.otc.models import Service
from transit_odp.otc.weca.registry import Registry

logger = getLogger(__name__)


class Loader:
    def __init__(self, registry: Registry):
        self.registry: Registry = registry

    def load(self):
        """
        Weca job will remove all the services from the database and re-insert all in DB
        Services present in WECA must be considered as registered, Other status will not be present
        """
        logger.info("WECA job to refresh all the services started")
        self.registry.process_services()
        if len(self.registry.services) > 0:
            self.delete_services()
            self.load_services()

        logger.info("WECA job finished the execution")

    def load_services(self):
        """
        Load all services in database by filling object
        """
        logger.info("Loading services into the database")
        service_objects = []
        for index, service in self.registry.services.iterrows():
            service_objects.append(Service(**service))

        Service.objects.bulk_create(service_objects)
        logger.info("WECA services inserted into the database")

    def delete_services(self):
        """
        Remove all the services with api_type WECA to reload all services
        """
        Service.objects.filter(api_type="WECA").delete()
