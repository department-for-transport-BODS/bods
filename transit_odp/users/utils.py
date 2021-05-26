from allauth.account.models import EmailAddress

from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory


# TODO - refactor into factory
def create_verified_org_user():
    org = OrganisationFactory.create(nocs=3)
    user = UserFactory.create(
        password="password",
        account_type=AccountType.org_admin.value,
        organisations=(org,),
    )
    # Normally a user would only be able to login if their email address has been
    # verified. However, the client login used in the test setup doesn't seem to
    # care but do it anyway
    EmailAddress.objects.update_or_create(
        defaults={"email": user.email, "verified": True, "primary": True}, user=user
    )
    return user
