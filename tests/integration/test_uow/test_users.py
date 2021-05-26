import pytest
from tests.integration.factories import (
    DeveloperFactory,
    OrganisationFactory,
    PublisherUserFactory,
    SiteAdminFactory,
)

from transit_odp.bods.domain.entities import User
from transit_odp.bods.domain.entities.identity import OrganisationId, UserId
from transit_odp.bods.domain.entities.user import Email, Publisher, SiteAdmin
from transit_odp.bods.service_layer.unit_of_work import UnitOfWork
from transit_odp.organisation import models as org_models
from transit_odp.users import models
from transit_odp.users.constants import AccountType

pytestmark = pytest.mark.django_db(transaction=True)


def create_developer(**kwargs) -> models.User:
    return DeveloperFactory(**kwargs)


def create_organisation(**kwargs) -> org_models.Organisation:
    return OrganisationFactory(**kwargs)


def create_publisher(organisation, **kwargs) -> models.User:
    user = PublisherUserFactory(organisations=(organisation,), **kwargs)
    organisation.key_contact = user
    organisation.save()
    return user


def create_site_admin(**kwargs) -> models.User:
    return SiteAdminFactory(**kwargs)


class TestUser:
    def test_uow_can_retrieve_an_user_by_id(self):
        record = create_developer()

        uow = UnitOfWork()
        with uow:
            user = uow.users.find(user_id=UserId(id=record.id))

        assert isinstance(user, User)
        assert user.id == UserId(id=record.id)

    def test_uow_returns_none_if_user_not_found(self):
        uow = UnitOfWork()
        with uow:
            user = uow.users.find(user_id=UserId(id=1000))
        assert user is None

    def test_uow_can_retrieve_a_user(self):
        record = create_developer()

        uow = UnitOfWork()
        with uow:
            [user] = uow.users.list()

        expected = User(
            id=UserId(id=record.id),
            email=record.email,
            mute_all_dataset_notifications=record.settings.mute_all_dataset_notifications,
        )
        assert isinstance(user, User)
        assert user == expected  # tests __eq__
        assert user.get_id() == record.id
        assert user.email == record.email

    @pytest.mark.parametrize(
        "account_type, is_admin, notify_avl_unavailable",
        [
            (AccountType.org_staff.value, False, False),
            (AccountType.org_admin.value, True, False),
        ],
        ids=["staff", "admin"],
    )
    def test_uow_can_retrieve_a_publisher(
        self, account_type, is_admin, notify_avl_unavailable
    ):
        organisation = create_organisation()
        record = create_publisher(account_type=account_type, organisation=organisation)

        uow = UnitOfWork()
        with uow:
            [user] = uow.users.list()

        expected = Publisher(
            id=UserId(id=record.id),
            email=record.email,
            mute_all_dataset_notifications=False,
            organisation_id=OrganisationId(id=record.organisation_id),
            is_admin=is_admin,
            notify_avl_unavailable=notify_avl_unavailable,
        )
        assert isinstance(user, Publisher)
        assert user == expected  # tests __eq__
        assert user.get_id() == record.id
        assert user.email == record.email
        assert user.organisation_id == OrganisationId(id=record.organisation_id)

    def test_uow_can_retrieve_a_site_admin(self):
        record = create_site_admin()

        uow = UnitOfWork()
        with uow:
            [user] = uow.users.list()

        expected = SiteAdmin(
            id=UserId(id=record.id),
            email=record.email,
            mute_all_dataset_notifications=record.settings.mute_all_dataset_notifications,
        )
        assert isinstance(user, SiteAdmin)
        assert user == expected  # tests __eq__
        assert user.get_id() == record.id
        assert user.email == record.email

    def test_uow_can_retrieve_publishers_for_organisation(self):
        organisation = create_organisation()
        user1 = create_publisher(organisation=organisation)
        user2 = create_publisher(organisation=organisation)
        another_organisation = create_organisation()
        create_publisher(organisation=another_organisation)

        uow = UnitOfWork()
        with uow:
            users = uow.users.list_members_of_organisation(
                organisation_id=OrganisationId(id=organisation.id)
            )

        assert sorted(user.get_id() for user in users) == [user1.id, user2.id]

    def test_uow_can_save_a_user(self):
        user = User(
            id=UserId(id=1),
            email=Email("user@test.com"),
            mute_all_dataset_notifications=False,
        )

        uow = UnitOfWork()
        with uow:
            uow.users.add(user)
            uow.commit()

        [record] = models.User.objects.all()
        assert record.id == user.get_id()
        assert record.email == user.email
        assert record.account_type == AccountType.developer.value

    def test_uow_can_save_a_publisher(self):
        organisation = create_organisation()
        user = Publisher(
            id=UserId(id=1),
            email=Email("user@test.com"),
            organisation_id=OrganisationId(id=organisation.id),
            is_admin=False,
            notify_avl_unavailable=False,
            mute_all_dataset_notifications=False,
        )

        uow = UnitOfWork()
        with uow:
            uow.users.add(user)
            uow.commit()

        [record] = models.User.objects.all()
        assert UserId(id=record.id) == user.id
        assert record.email == user.email
        assert OrganisationId(id=record.organisation_id) == user.organisation_id
        assert record.account_type == AccountType.org_staff.value

    def test_uow_can_save_a_site_admin(self):
        user = SiteAdmin(
            id=UserId(id=1),
            email=Email("user@test.com"),
            mute_all_dataset_notifications=False,
        )

        uow = UnitOfWork()
        with uow:
            uow.users.add(user)
            uow.commit()

        [record] = models.User.objects.all()
        assert UserId(id=record.id) == user.id
        assert record.email == user.email
        assert record.account_type == AccountType.site_admin.value
