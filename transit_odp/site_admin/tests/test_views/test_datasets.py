import pytest
from django_hosts import reverse

from config.hosts import ADMIN_HOST
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import Dataset
from transit_odp.users.constants import SiteAdminType

pytestmark = pytest.mark.django_db

# TODO Improve unit test coverage here!


def test_org_timetables_ordering(client_factory, user_factory):
    org = OrganisationFactory()
    DatasetRevisionFactory.create_batch(5, dataset__organisation=org)
    user = user_factory(account_type=SiteAdminType)

    url = reverse(
        "users:organisation-timetables-list", kwargs={"pk": org.id}, host=ADMIN_HOST
    )
    client = client_factory(host=ADMIN_HOST)
    client.force_login(user)

    response = client.get(url, data={"ordering": "name"})

    assert list(response.context_data["object_list"]) == list(
        Dataset.objects.all().order_by("live_revision__name")
    )


def test_org_timetables_ordering_not_specified(client_factory, user_factory):
    org = OrganisationFactory()
    DatasetRevisionFactory.create_batch(5, dataset__organisation=org)
    user = user_factory(account_type=SiteAdminType)

    url = reverse(
        "users:organisation-timetables-list", kwargs={"pk": org.id}, host=ADMIN_HOST
    )
    client = client_factory(host=ADMIN_HOST)
    client.force_login(user)

    response = client.get(url)

    assert list(response.context_data["object_list"]) == list(
        Dataset.objects.all().order_by("-modified")
    )
