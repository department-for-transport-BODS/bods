import logging
from datetime import datetime
from transit_odp.otc.models import Service, LocalAuthority

from transit_odp.otc.client import OTCAPIClient

logger = logging.getLogger(__name__)


class PopulateLTA:
    def __init__(self):
        self._client = OTCAPIClient()

    def populate_lta(self, registrations_from_service, total_count):
        current_processing_count = 0
        for registration_from_service in registrations_from_service:
            unique_local_authorities = set()
            service_id = registration_from_service[0]
            logger.info(
                f"Requesting OTC API for LTA name(s) for registration number - {registration_from_service[1]} and lta id is {service_id}"
            )
            try:
                registrations = self._client.get_lta_names_by_registration_codes(
                    registration_from_service[1]
                )
            except Exception as e:
                logger.error(
                    f"Error for registration number: {registration_from_service[1]}, error message: {e}"
                )
            if registrations:
                for reg in registrations:
                    if reg.local_authorities is not None:
                        unique_local_authorities.add(reg.local_authorities)
                    else:
                        unique_local_authorities.add("")

                for local_authority in unique_local_authorities:
                    logger.info(f"Unique local authority is: {local_authority}")
                    lta, created = LocalAuthority.objects.get_or_create(name=local_authority)
                    if created:
                        logger.info("LocalAuthority object created")
                    else:
                        logger.info("LocalAuthority object exists")
                    
                    lta.registration_numbers.add(service_id)
                current_processing_count += 1
                logger.info(f"Completed {current_processing_count} of {total_count}")

    def refresh(self, registrations):
        """
        The method is used to update the database with updated local authorites from latest variations.
        """
        for registration in registrations:
            logger.info(f"The registration is :>>>>>{registration}")
            unique_local_authorities = set()
            _service = Service.objects.filter(
                registration_number=registration.registration_number
            ).values_list("id")
            if _service:
                service_id = _service[0][0]
                logger.info(
                    f"New registration that need update is: {registration.registration_number} and related service id is - {service_id}"
                )
                if registration.local_authorities is not None:
                    unique_local_authorities.add(registration.local_authorities)
                else:
                    unique_local_authorities.add("")
                logger.info(f"Unique local authority is: {unique_local_authorities}")

                for local_authority in unique_local_authorities:
                    logger.info(f"Unique local authority is: {local_authority}")
                    lta, created = LocalAuthority.objects.get_or_create(name=local_authority)
                    if created:
                        logger.info("LocalAuthority object created")
                    else:
                        logger.info("LocalAuthority object exists")
                    lta.registration_numbers.add(service_id)

