import logging
from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel
from stories import Result, Success, arguments, story

from transit_odp.bods.domain import commands
from transit_odp.bods.domain.entities import AVLPublication
from transit_odp.bods.domain.services import AVLFeedWatcher
from transit_odp.bods.interfaces.unit_of_work import IUnitOfWork
from transit_odp.organisation.constants import DatasetType

logger = logging.getLogger(__name__)


@dataclass
class MonitorAVLFeeds:
    """
    Retrieve status of AVLFeeds and notify the publisher if their feed has gone down
    """

    def __call__(self, command):
        with self.uow:
            result = self.story.run(command=command)
            if result.is_success:
                self.uow.commit()

    @story
    @arguments("command")
    def story(I):  # noqa
        I.get_publications
        I.run_avl_feed_watcher
        I.persist_updates

    # Dependencies
    uow: IUnitOfWork
    avl_feed_watcher: AVLFeedWatcher

    # Steps
    def get_publications(self, ctx):
        ctx.publications = self.uow.publications.list(dataset_types=[DatasetType.AVL])
        return Success()

    def run_avl_feed_watcher(self, ctx):
        ctx.publications_changed = list(self.avl_feed_watcher.run(ctx.publications))
        return Success()

    def persist_updates(self, ctx):
        if len(ctx.publications_changed) == 0:
            return Result()  # ends story

        for pub in ctx.publications_changed:
            self.uow.publications.update(pub)

        return Success()


@MonitorAVLFeeds.story.contract
class Context(BaseModel):
    # Arguments
    command: commands.MonitorAVLFeeds

    # State
    publications: Sequence[AVLPublication]
    publications_changed: Sequence[AVLPublication]
