from typing import Any, Sequence

from django.contrib.auth import get_user_model
from django.utils import timezone
from factory import (
    DjangoModelFactory,
    Faker,
    LazyAttributeSequence,
    SubFactory,
    lazy_attribute,
    post_generation,
)

from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import (
    AgentUserType,
    DeveloperType,
    OrgAdminType,
    OrgStaffType,
    SiteAdminType,
)
from transit_odp.users.models import AgentUserInvite, Invitation

ORG_USER_TYPES = [AgentUserType, OrgAdminType, OrgStaffType]


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]

    username = Faker("user_name")
    email = LazyAttributeSequence(
        lambda obj, n: f"{obj.first_name}.{obj.last_name}{n}@example.com"
    )
    account_type = DeveloperType
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    # token - Created automatically by post save signal
    # settings - Created automatically by post save signal

    @post_generation
    def name(self, create: bool, extracted: Sequence[Any], **kwargs):
        name = extracted
        if name is None:
            self.name = f"{self.first_name} {self.last_name}"

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = extracted
        if password is None:
            password = Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).generate(extra_kwargs={})
        self.set_password(password)

    @post_generation
    def organisations(self, create, extracted, **kwargs):
        if not create or self.account_type not in ORG_USER_TYPES:
            return None

        if extracted:
            for organisation in extracted:
                self.organisations.add(organisation)
        else:
            self.organisations.add(OrganisationFactory())

    @post_generation
    def verified(self, create: bool, extracted: bool, **kwargs):
        """Verifies the user's email address so they can login via the Client.
        Defaults to True"""
        if extracted is None:
            extracted = True
        if extracted and create:
            self.emailaddress_set.update_or_create(
                defaults={"verified": True, "primary": True}, email=self.email
            )


class OrgAdminFactory(UserFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]

    account_type = OrgAdminType


class OrgStaffFactory(UserFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]

    account_type = OrgStaffType


class AgentUserFactory(UserFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]

    account_type = AgentUserType

    @post_generation
    def organisations(self, create, extracted, **kwargs):
        if not create or self.account_type != AgentUserType:
            return None

        if extracted:
            for organisation in extracted:
                self.organisations.add(organisation)
        else:
            self.organisations.add(OrganisationFactory())


class InvitationFactory(DjangoModelFactory):
    class Meta:
        model = Invitation

    email = Faker("email")
    inviter = SubFactory(UserFactory, account_type=SiteAdminType)
    account_type = DeveloperType
    is_key_contact = False
    sent = timezone.now()
    accepted = False

    @lazy_attribute
    def organisation(self):
        if self.account_type in ORG_USER_TYPES:
            return OrganisationFactory()
        else:
            return None


class AgentUserInviteFactory(DjangoModelFactory):
    class Meta:
        model = AgentUserInvite

    agent = SubFactory(UserFactory, account_type=AgentUserType)
    organisation = SubFactory(OrganisationFactory)
    inviter = SubFactory(UserFactory, account_type=OrgAdminType)
    invitation = None
    status = AgentUserInvite.PENDING
