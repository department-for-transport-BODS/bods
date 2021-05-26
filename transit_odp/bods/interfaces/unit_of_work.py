from typing import Protocol

from transit_odp.bods.interfaces.repository import (
    IOrganisationRepository,
    IPublicationRepository,
    IUserRepository,
)


class IUnitOfWork(Protocol):
    publications: IPublicationRepository
    users: IUserRepository
    organisations: IOrganisationRepository

    def __enter__(self) -> "IUnitOfWork":
        return self.start()

    def __exit__(self, *args):
        self.rollback()

    def start(self) -> "IUnitOfWork":
        return self

    def commit(self):
        ...

    def rollback(self):
        ...

    def collect_new_events(self):
        for product in self.publications.seen:
            while product.events:
                yield product.events.pop(0)
