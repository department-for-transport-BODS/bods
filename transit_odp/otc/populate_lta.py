import logging
from datetime import datetime
from transit_odp.otc.models import Service, LocalAuthority

from transit_odp.otc.client import OTCAPIClient

logger = logging.getLogger(__name__)


class PopulateLTA:
    def __init__(self):
        self._client = OTCAPIClient()

    def populate_lta(self, registrations_from_service, total_count):
        logger.info(f"Requesting OTC API for all services with latest variations")
        try:
            registrations = self._client.get_all_lta_names_latest_variations()
        except Exception as e:
            logger.error(f"Error while fetching otc records, error message: {e}")
        logger.info(f"The length of total registrations is {len(registrations)}")
        registrations_from_service = ["PB0000006/4", "PB0000006/7", "PB0000006/2"]
        if registrations:
            current_processing_count = 0
            for registration_from_service in registrations_from_service:
                unique_local_authorities = set()
                service_id = 13566
                filtered_results = []
                for registration in registrations:
                    if registration.registration_number == registration_from_service:
                        filtered_results.append(registration)
                logger.info(f"Filtered result is {filtered_results}")
                if filtered_results:
                    for reg in filtered_results:
                        if "|" in reg.local_authorities:
                            authorities = reg.local_authorities.split("|")
                            unique_local_authorities.update(authorities)
                        else:
                            unique_local_authorities.add(reg.local_authorities)
                    for local_authority in unique_local_authorities:
                        logger.info(f"Unique local authority is: {local_authority}")
                        lta, created = LocalAuthority.objects.get_or_create(
                            name=local_authority
                        )
                        if created:
                            logger.info("LocalAuthority object created")
                        else:
                            logger.info("LocalAuthority object exists")

                        lta.registration_numbers.add(service_id)
                    current_processing_count += 1
                    logger.info(
                        f"Completed {current_processing_count} of {total_count}"
                    )

    def refresh(self, registrations):
        """
        The method is used to update the database with updated local authorites from latest variations.
        """
        for registration in registrations:
            logger.info(f"Started executuion for registration: {registration}")
            unique_local_authorities = set()
            _service = Service.objects.filter(
                registration_number=registration.registration_number
            ).values_list("id")
            if _service:
                _service_id = _service[0][0]
                logger.info(
                    f"Deleting LTA mapping for service ID: {_service_id} from the LTA relationship"
                )
                _ = LocalAuthority.objects.filter(
                    registration_numbers=_service_id
                ).delete()
                logger.info(
                    f"New registration that need update is: {registration.registration_number} and related service id is - {_service_id}"
                )
                if registration.local_authorities is not None:
                    if "|" in registration.local_authorities:
                        authorities = registration.local_authorities.split("|")
                        unique_local_authorities.update(authorities)
                    else:
                        unique_local_authorities.add(registration.local_authorities)
                else:
                    unique_local_authorities.add("")
                for local_authority in unique_local_authorities:
                    logger.info(f"Unique local authority is: {local_authority}")
                    lta, created = LocalAuthority.objects.get_or_create(
                        name=local_authority
                    )
                    if created:
                        logger.info("LocalAuthority object created")
                    else:
                        logger.info("LocalAuthority object exists")
                    lta.registration_numbers.add(_service_id)
