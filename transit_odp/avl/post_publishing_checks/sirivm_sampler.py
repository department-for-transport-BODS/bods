import logging
import random
from typing import List, Optional, Tuple

import requests
from django.conf import settings

from transit_odp.avl.post_publishing_checks.constants import SirivmField
from transit_odp.avl.post_publishing_checks.models import Siri, VehicleActivity

logger = logging.getLogger(__name__)


class SiriHeader(dict):
    def __setitem__(self, key, value):
        if key not in SirivmField:
            raise KeyError("Key must be in SirivmField enumeration")
        dict.__setitem__(self, key, value)

    @classmethod
    def from_siri_packet(cls, siri: Siri):
        siri_header = cls()
        siri_header[SirivmField.VERSION] = siri.version
        siri_header[
            SirivmField.RESPONSE_TIMESTAMP_SD
        ] = siri.service_delivery.response_timestamp
        siri_header[SirivmField.PRODUCER_REF] = siri.service_delivery.producer_ref
        vmd = siri.service_delivery.vehicle_monitoring_delivery
        siri_header[SirivmField.RESPONSE_TIMESTAMP_VMD] = vmd.response_timestamp
        siri_header[SirivmField.REQUEST_MESSAGE_REF] = vmd.request_message_ref
        siri_header[SirivmField.VALID_UNTIL] = vmd.valid_until
        siri_header[SirivmField.SHORTEST_POSSIBLE_CYCLE] = vmd.shortest_possible_cycle
        return siri_header


class SirivmSampler:
    def get_siri_vm_data_feed_by_id(self, feed_id: int) -> Optional[bytes]:
        url = f"{settings.CAVL_CONSUMER_URL}/datafeed/{feed_id}/"
        try:
            response = requests.get(url, timeout=60)
        except requests.RequestException:
            logger.exception(f"Error requesting {url}")
            return None

        if response.status_code != 200:
            logger.error(f"Status code {response.status_code} returned from GET {url}")
            return None

        return response.content

    def get_vehicle_activities(
        self,
        feed_id: int,
        num_activities: int,
    ) -> Tuple[SiriHeader, List[VehicleActivity]]:
        random.seed()
        sirivm_fields = {}
        feed = self.get_siri_vm_data_feed_by_id(feed_id=feed_id)
        if not isinstance(feed, bytes):
            return sirivm_fields, []

        siri = Siri.from_bytes(feed)
        sirivm_header = SiriHeader.from_siri_packet(siri)

        vmd = siri.service_delivery.vehicle_monitoring_delivery
        vehicle_activities = vmd.vehicle_activities
        logger.info(
            f"Client returned {len(vehicle_activities)} vehicle activities for "
            f"feed {feed_id}"
        )
        if len(vehicle_activities) == 0:
            return sirivm_header, []

        num_samples = min(num_activities, len(vehicle_activities))
        samples = random.sample(vehicle_activities, k=num_samples)

        logger.debug(
            f"Added {len(samples)} sample vehicle activities for feed id {feed_id}"
        )
        return sirivm_header, samples
