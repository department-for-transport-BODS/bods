from logging import getLogger

from transit_odp.otc.constants import API_TYPE_WECA
from transit_odp.otc.models import Licence, Service
from transit_odp.otc.weca.registry import Registry

logger = getLogger(__name__)


class Loader:
    def __init__(self, registry: Registry):
        self.registry: Registry = registry
        self.licences = {}

    def load(self):
        """
        Weca job will remove all the services from the database and re-insert all in DB
        Services present in WECA must be considered as registered, Other status will not be present
        Some licences in weca might be missing from the database, job will create those licences and
        Will bind those licences to the weca services being created
        """
        logger.info("WECA job to refresh all the services started")
        self.registry.process_services()
        self.licences = self.load_missing_licences()
        if len(self.registry.services) > 0:
            self.delete_services()
            self.load_services()

        logger.info("WECA job finished the execution")

    def load_missing_licences(self):
        logger.info("Loading missing licences")
        missing_licences = self.registry.get_missing_licences()
        licences = {}
        if len(missing_licences) == 0:
            logger.info("Found 0 Licences missing")
            return licences

        logger.info(f"Found {len(missing_licences)} missing licences")
        for licence in missing_licences:
            licences[licence] = Licence.objects.create(
                number=licence, status="Valid"
            ).id

        return licences

    def load_services(self):
        """
        Load all services in database by filling object
        If licence_id is null, licence is missing in the database
        service will check it in the licences property and
        assign licence_id to the service object
        """
        logger.info("Loading services into the database")
        service_objects = []
        for index, service in self.registry.services.iterrows():
            if not service["licence_id"]:
                service["licence_id"] = self.licences.get(service["licence"], None)
            service.drop(["licence"], inplace=True)
            service_objects.append(Service(**service))

        Service.objects.bulk_create(service_objects)
        logger.info("WECA services inserted into the database")

    def delete_services(self):
        """
        Remove all the services with api_type WECA to reload all services
        """
        Service.objects.filter(api_type=API_TYPE_WECA).delete()
