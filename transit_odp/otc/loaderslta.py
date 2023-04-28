from logging import getLogger

from django.db import transaction

from transit_odp.otc.models import Service, LocalAuthority

from transit_odp.otc.populate_lta import PopulateLTA

logger = getLogger(__name__)


class LoadFailedException(Exception):
    pass


class LoaderLTA:
    def __init__(self, populate_lta: PopulateLTA):
        self.populate_lta: PopulateLTA = populate_lta

    def _delete_all_lta_data(self) -> None:
        logger.info("Clearing LocalAuthority table")
        count, _ = LocalAuthority.objects.all().delete()
        logger.info(f"Deleted {count} OTC Local Authorities")

    @transaction.atomic
    def load_lta_into_fresh_database(self):
        logger.info(f"Deleting all LocalAuthory objects from the database")
        self._delete_all_lta_data()

        logger.info(f"Getting all registration numbers from the Service table")
        registration_numbers = Service.objects.values_list("id", "registration_number")
        if registration_numbers:
            count = len(registration_numbers)
            logger.info(f"Total count of registration numbers is {count}")
            self.populate_lta.populate_lta(registration_numbers, count)
        logger.info(f"Loading local authority data completed")
