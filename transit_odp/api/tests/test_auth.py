import pytest

from transit_odp.api.views.auth import _serialize_user
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import AgentUserFactory, UserFactory


pytestmark = pytest.mark.django_db


def test_serialize_user_includes_routing_fields_for_org_user():
    organisation = OrganisationFactory()
    user = UserFactory(
        account_type=AccountType.org_admin.value,
        organisations=(organisation,),
    )

    payload = _serialize_user(user)

    assert payload["account_type"] == AccountType.org_admin.value
    assert payload["organisation_id"] == organisation.id
    assert payload["is_org_user"] is True
    assert payload["is_single_org_user"] is True
    assert payload["is_agent_user"] is False


def test_serialize_user_includes_routing_fields_for_agent_user():
    organisation = OrganisationFactory()
    user = AgentUserFactory(organisations=(organisation,))

    payload = _serialize_user(user)

    assert payload["account_type"] == AccountType.agent_user.value
    assert payload["organisation_id"] == organisation.id
    assert payload["is_org_user"] is True
    assert payload["is_single_org_user"] is False
    assert payload["is_agent_user"] is True
