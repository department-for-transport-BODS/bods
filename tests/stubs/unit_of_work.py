from tests.stubs.repository import (
    FakeOrganisationRepository,
    FakePublicationRepository,
    FakeUserRepository,
)

from transit_odp.bods.interfaces.unit_of_work import IUnitOfWork


class FakeUnitOfWork(IUnitOfWork):
    def __init__(self):
        self.publications = FakePublicationRepository([])
        self.users = FakeUserRepository()
        self.organisations = FakeOrganisationRepository()
        self.committed = False

    def commit(self):
        # We can check this attribute to see if our function under test commits the UoW
        self.committed = True

    def rollback(self):
        pass
