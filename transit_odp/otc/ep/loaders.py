from logging import getLogger

from transit_odp.otc.constants import API_TYPE_EP
from transit_odp.otc.models import Licence, Service
from transit_odp.otc.ep.registry import Registry

logger = getLogger(__name__)


class Loader:
    def __init__(self, registry: Registry):
        self.registry: Registry = registry
        self.licences = {}

    def load(self):
        """
        EP job will remove all the services from the database and re-insert all in DB
        Services present in EP must be considered as registered, Other status will not be present
        Some licences in EP might be missing from the database, job will create those licences and
        Will bind those licences to the EP services being created
        """
        logger.info("EP job to refresh all the services started")
        self.registry.process_services()
        self.licences = self.load_missing_licences()
        if len(self.registry.services) > 0:
            self.delete_services()
            self.load_services()

        logger.info("EP job finished the execution")

    def load_missing_licences(self) -> dict:
        """
        This function is used to load missing licences.

        Returns:
            dict: A dictionary where the keys are the licence numbers and the values are the IDs of the Licence objects.
        """
        logger.info("Loading missing licences")
        missing_licences = self.registry.get_missing_licences()
        licences = {}
        if len(missing_licences) == 0:
            logger.info("No Licences missing")
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
        service will check it in the licences property andx
        assign licence_id to the service object
        """
        logger.info("Loading services into the database")
        service_objects = []
        for _, service in self.registry.services.iterrows():
            if not service["licence_id"]:
                service["licence_id"] = self.licences.get(service["licence"], None)
            service.drop(["licence"], inplace=True)
            service_objects.append(Service(**service))

        Service.objects.bulk_create(service_objects)
        logger.info("EP services inserted into the database")

    def delete_services(self):
        """
        Remove all the services with api_type EP to reload all services
        """
        Service.objects.filter(api_type=API_TYPE_EP).delete()
