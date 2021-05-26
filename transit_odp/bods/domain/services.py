import logging
from dataclasses import dataclass
from typing import Iterable, List

from transit_odp.bods.domain.entities import AVLPublication
from transit_odp.bods.interfaces.gateways import ICAVLService

logger = logging.getLogger(__name__)


@dataclass
class AVLFeedWatcher:
    cavl_service: ICAVLService

    def run(self, publications: List[AVLPublication]) -> Iterable[AVLPublication]:
        """Fetches latest state from CAVL and updates the AVLPublication"""
        avl_feeds = self.cavl_service.get_feeds()
        avl_status_lookup = {avl_feed.id: avl_feed.status for avl_feed in avl_feeds}

        for publication in publications:
            new_status = avl_status_lookup.get(publication.get_id())

            if new_status is None:
                # TODO - this is probably an error / mismatch in state between BODS/CAVL
                logger.debug(f"Did not retrieve AVLFeed status for {publication}")
                continue

            publication.update_feed_status(new_status)
            yield publication
