from functools import cached_property
from logging import getLogger
from typing import Set, Tuple, Union

from django.db import transaction

from transit_odp.otc.client.enums import RegistrationStatusEnum
from transit_odp.otc.models import Licence, Operator, Service, LocalAuthority

from transit_odp.otc.registry import Registry
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
        count = len(registration_numbers)
        logger.info(f"Total count of registration numbers is {count}")
        self.populate_lta.populate_lta(registration_numbers)

    def load_updated_lta(self):
        """
        The method is used to get the records that have been updated in OTC API and then updates the database.
        """
        most_recently_modified = (
            Service.objects.filter(last_modified__isnull=False)
            .order_by("last_modified")
            .last()
        )
        if (
            most_recently_modified is None
            or most_recently_modified.last_modified is None
        ):
            logger.error("Can't find last modified date in database, terminating")
            raise LoadFailedException("Cannot calculate last run date of task")

        with transaction.atomic():
            self.populate_lta.refresh(most_recently_modified.last_modified)

    @cached_property
    def registered_service(self):
        return self.registry.filter_by_status(RegistrationStatusEnum.REGISTERED.value)
