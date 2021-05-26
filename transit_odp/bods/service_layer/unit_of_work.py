from django.db import DatabaseError, transaction

from transit_odp.bods.adapters import repositories
from transit_odp.bods.interfaces.unit_of_work import IUnitOfWork


class UnitOfWork(IUnitOfWork):
    def __exit__(self, *args):
        super().__exit__(*args)
        transaction.set_autocommit(True)

    def start(self) -> "IUnitOfWork":
        self.publications = repositories.PublicationRepository()
        self.users = repositories.UserRepository()
        self.organisations = repositories.OrganisationRepository()
        transaction.set_autocommit(False)
        return super().start()

    def commit(self):
        try:
            transaction.commit()
        except (DatabaseError, Exception):
            self.rollback()
        transaction.set_autocommit(True)

    def rollback(self):
        transaction.rollback()
        transaction.set_autocommit(True)
