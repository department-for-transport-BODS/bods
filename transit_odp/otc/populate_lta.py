import logging
from datetime import datetime
from transit_odp.otc.models import Service, LocalAuthority

from transit_odp.otc.client import OTCAPIClient

logger = logging.getLogger(__name__)


class PopulateLTA: 
    def __init__(self):
        self._client = OTCAPIClient()

    def populate_lta(self, registrations_from_service):
        for registration_from_service in registrations_from_service:
            logger.info(f"The registration looks like {registration_from_service[1]}")
            lta_id = registration_from_service[0]
            logger.info(f"Requesting OTC API for LTA name(s) for registration number - {registration_from_service[1]} and lta id is {lta_id}")
            try:
                registrations = self._client.get_lta_names_by_registration_codes(registration_from_service[1])
            except Exception as e:
                logger.error(f"Error for registration number: {registration_from_service[1]}, error message: {e}")
            unique_local_authorities = set(reg.local_authorities for reg in registrations)
            unique_local_authorities = {"" if value is None else value for value in unique_local_authorities}
            for local_authority in unique_local_authorities:
                logger.info(f"Unique local authority is: {local_authority}")
                lta = LocalAuthority.objects.create(name=local_authority)
                lta.registration_numbers.add(lta_id)
        logger.info("Populating LocalAuthority completed")

    def refresh(self, when: datetime):
        """
        The method is used to update the database with updated local authorites from latest variations.
        """
        logger.info(f"Querying the OTC API to get the latest variations")
        for registrations in self._client.get_latest_variations_since(when):
            service_id = Service.objects.filter(registration_number=registrations.registration_number).values_list("id")
            logger.info(f"New registration that need update is: {registrations.registration_number}")
            unique_local_authorities = set(registrations.local_authorities)
            unique_local_authorities = {"" if value is None else value for value in unique_local_authorities}
            for local_authority in unique_local_authorities:
                logger.info(f"Unique local authority is: {local_authority}")
                lta, created = LocalAuthority.objects.get_or_create(local_authority)
                if created:
                    logger.info("LocalAuthority created")
                else:
                    logger.ino("LocalAuthority exists")
                lta.registration_numbers.add(service_id)
        logger.info("LocalAuthority refresh completed")


