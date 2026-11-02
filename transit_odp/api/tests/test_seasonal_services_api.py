import datetime
import json

import pytest

from config import hosts
from transit_odp.organisation.factories import (
    LicenceFactory,
    OrganisationFactory,
    SeasonalServiceFactory,
)
from transit_odp.organisation.models import SeasonalService
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import AgentUserFactory, UserFactory

pytestmark = pytest.mark.django_db

FUTURE_START = datetime.date.today() + datetime.timedelta(days=30)
FUTURE_END = datetime.date.today() + datetime.timedelta(days=60)


def _post(client, url, **body):
    return client.post(url, data=json.dumps(body), content_type="application/json")


@pytest.fixture
def org_context(client_factory):
    organisation = OrganisationFactory()
    user = UserFactory(
        account_type=AccountType.org_staff.value, organisations=(organisation,)
    )
    licence = LicenceFactory(organisation=organisation)
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=user)
    return client, organisation, licence, user


@pytest.fixture
def other_org_client(client_factory):
    other_org = OrganisationFactory()
    user = UserFactory(
        account_type=AccountType.org_staff.value, organisations=(other_org,)
    )
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=user)
    return client


def _endpoints(org_id, service_id=1):
    return [
        ("get", f"/api/seasonal-services/{org_id}/"),
        ("get", f"/api/seasonal-services/{org_id}/licences/"),
        ("post", f"/api/seasonal-services/{org_id}/validate-licence/"),
        ("post", f"/api/seasonal-services/{org_id}/create/"),
        ("post", f"/api/seasonal-services/{org_id}/delete/"),
        ("get", f"/api/seasonal-services/{org_id}/{service_id}/"),
        ("post", f"/api/seasonal-services/{org_id}/{service_id}/update/"),
    ]


def _call(client, method, url):
    if method == "get":
        return client.get(url)
    return _post(client, url)


@pytest.mark.parametrize("index", range(7))
def test_endpoints_require_authentication(client_factory, index):
    organisation = OrganisationFactory()
    client = client_factory(host=hosts.PUBLISH_HOST)
    method, url = _endpoints(organisation.id)[index]

    response = _call(client, method, url)

    assert response.status_code == 401
    assert response.json() == {"error": "Authentication required"}


@pytest.mark.parametrize("index", range(7))
def test_endpoints_are_forbidden_for_another_organisation(other_org_client, index):
    organisation = OrganisationFactory()
    method, url = _endpoints(organisation.id)[index]

    response = _call(other_org_client, method, url)

    assert response.status_code == 403


def test_endpoints_are_forbidden_for_abods_users(client_factory):
    organisation = OrganisationFactory()
    user = UserFactory(
        account_type=AccountType.abods_user.value, organisations=(organisation,)
    )
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=user)

    response = client.get(f"/api/seasonal-services/{organisation.id}/")

    assert response.status_code == 403


def test_list_returns_empty_state(org_context):
    client, organisation, _licence, _user = org_context

    response = client.get(f"/api/seasonal-services/{organisation.id}/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["organisationName"] == organisation.name
    assert payload["isAgentUser"] is False
    assert payload["counter"] == 0
    assert payload["results"] == []
    assert payload["sort"] == "service_ends"
    assert payload["pagination"] == {
        "page": 1,
        "totalPages": 1,
        "count": 0,
        "pageSize": 10,
    }


def test_list_returns_camel_case_rows_for_the_organisation_only(org_context):
    client, organisation, licence, _user = org_context
    service = SeasonalServiceFactory(
        licence=licence,
        registration_code=12,
        start=datetime.date(2023, 3, 4),
        end=datetime.date(2023, 6, 7),
    )
    SeasonalServiceFactory()  # another organisation

    response = client.get(f"/api/seasonal-services/{organisation.id}/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["counter"] == 1
    assert payload["results"] == [
        {
            "id": service.id,
            "licenceNumber": licence.number,
            "registrationCode": 12,
            "serviceCode": f"{licence.number}/12",
            "start": "2023-03-04",
            "end": "2023-06-07",
            "serviceBegins": "04/03/2023",
            "serviceEnds": "07/06/2023",
        }
    ]


def test_list_is_ordered_by_end_date_and_paginated(org_context):
    client, organisation, licence, _user = org_context
    for index in range(13):
        SeasonalServiceFactory(
            licence=licence,
            registration_code=100 + index,
            start=datetime.date(2023, 1, 1),
            end=datetime.date(2023, 2, 1) + datetime.timedelta(days=index),
        )

    first = client.get(f"/api/seasonal-services/{organisation.id}/").json()
    second = client.get(f"/api/seasonal-services/{organisation.id}/?page=2").json()
    clamped = client.get(f"/api/seasonal-services/{organisation.id}/?page=99").json()
    invalid = client.get(f"/api/seasonal-services/{organisation.id}/?page=abc").json()

    assert [row["registrationCode"] for row in first["results"]] == list(
        range(100, 110)
    )
    assert first["pagination"]["totalPages"] == 2
    assert [row["registrationCode"] for row in second["results"]] == [110, 111, 112]
    assert clamped["pagination"]["page"] == 2
    assert invalid["pagination"]["page"] == 1


def test_list_sorts_by_requested_column(org_context):
    client, organisation, licence, _user = org_context
    for code in (3, 1, 2):
        SeasonalServiceFactory(licence=licence, registration_code=code)

    ascending = client.get(
        f"/api/seasonal-services/{organisation.id}/?sort=service_code"
    ).json()
    descending = client.get(
        f"/api/seasonal-services/{organisation.id}/?sort=-service_code"
    ).json()
    unknown = client.get(f"/api/seasonal-services/{organisation.id}/?sort=bogus").json()

    assert [r["registrationCode"] for r in ascending["results"]] == [1, 2, 3]
    assert ascending["sort"] == "service_code"
    assert [r["registrationCode"] for r in descending["results"]] == [3, 2, 1]
    assert descending["sort"] == "-service_code"
    assert unknown["sort"] == "service_ends"


def test_list_flags_agent_users(client_factory):
    organisation = OrganisationFactory()
    agent = AgentUserFactory()
    agent.organisations.add(organisation)
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=agent)

    response = client.get(f"/api/seasonal-services/{organisation.id}/")

    assert response.status_code == 200
    assert response.json()["isAgentUser"] is True


def test_licences_lists_only_organisation_licences(org_context):
    client, organisation, licence, _user = org_context
    LicenceFactory()

    response = client.get(f"/api/seasonal-services/{organisation.id}/licences/")

    assert response.status_code == 200
    assert response.json()["licences"] == [{"id": licence.id, "number": licence.number}]


def test_validate_licence_accepts_organisation_licence(org_context):
    client, organisation, licence, _user = org_context

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/validate-licence/",
        licence=licence.id,
    )

    assert response.status_code == 200
    assert response.json() == {"licence": {"id": licence.id, "number": licence.number}}


@pytest.mark.parametrize("licence", [None, "", 999999])
def test_validate_licence_rejects_missing_or_foreign_licence(org_context, licence):
    client, organisation, _licence, _user = org_context

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/validate-licence/",
        licence=licence,
    )

    assert response.status_code == 400
    assert "licence" in response.json()["field_errors"]


def test_validate_licence_rejects_licence_of_another_organisation(org_context):
    client, organisation, _licence, _user = org_context
    foreign = LicenceFactory()

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/validate-licence/",
        licence=foreign.id,
    )

    assert response.status_code == 400


def test_validate_licence_error_message_matches_django(org_context):
    client, organisation, _licence, _user = org_context

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/validate-licence/",
        licence="",
    )

    assert response.json()["field_errors"] == {"licence": ["This field is required."]}


def test_create_adds_seasonal_service(org_context):
    client, organisation, licence, _user = org_context

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/create/",
        licence=licence.id,
        registrationCode=42,
        start=FUTURE_START.isoformat(),
        end=FUTURE_END.isoformat(),
    )

    assert response.status_code == 201
    service = SeasonalService.objects.get(id=response.json()["id"])
    assert service.licence == licence
    assert service.registration_code == 42
    assert service.start == FUTURE_START
    assert service.end == FUTURE_END


def test_create_returns_django_validation_messages(org_context):
    client, organisation, licence, _user = org_context

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/create/",
        licence=licence.id,
        registrationCode="",
        start=FUTURE_END.isoformat(),
        end=FUTURE_START.isoformat(),
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]
    assert body["field_errors"] == {
        "registrationCode": ["Enter a service code in the box below"],
        "end": ["Start date must be earlier than end date"],
    }
    assert SeasonalService.objects.count() == 0


def test_create_requires_dates(org_context):
    client, organisation, licence, _user = org_context

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/create/",
        licence=licence.id,
        registrationCode=1,
    )

    assert response.status_code == 400
    assert response.json()["field_errors"] == {
        "start": ["This date is required"],
        "end": ["This date is required"],
    }


def test_create_rejects_end_date_in_the_past(org_context):
    client, organisation, licence, _user = org_context

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/create/",
        licence=licence.id,
        registrationCode=1,
        start="2020-01-01",
        end="2020-02-01",
    )

    assert response.status_code == 400
    assert response.json()["field_errors"] == {
        "end": ["End date cannot be in the past"]
    }


def test_create_rejects_invalid_dates(org_context):
    client, organisation, licence, _user = org_context

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/create/",
        licence=licence.id,
        registrationCode=1,
        start="not-a-date",
        end="also-not",
    )

    assert response.status_code == 400
    errors = response.json()["field_errors"]
    assert errors["start"] == ["Error first date"]
    assert errors["end"] == ["Error last date"]


def test_create_rejects_duplicate_service_code_for_licence(org_context):
    client, organisation, licence, _user = org_context
    SeasonalServiceFactory(licence=licence, registration_code=7)

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/create/",
        licence=licence.id,
        registrationCode=7,
        start=FUTURE_START.isoformat(),
        end=FUTURE_END.isoformat(),
    )

    assert response.status_code == 400
    assert response.json()["field_errors"] == {
        "registrationCode": [
            "This service code has already been set up with a date range"
        ]
    }


def test_create_rejects_licence_of_another_organisation(org_context):
    client, organisation, _licence, _user = org_context
    foreign = LicenceFactory()

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/create/",
        licence=foreign.id,
        registrationCode=1,
        start=FUTURE_START.isoformat(),
        end=FUTURE_END.isoformat(),
    )

    assert response.status_code == 400
    assert "licence" in response.json()["field_errors"]
    assert SeasonalService.objects.count() == 0


def test_detail_returns_service(org_context):
    client, organisation, licence, _user = org_context
    service = SeasonalServiceFactory(licence=licence, registration_code=5)

    response = client.get(f"/api/seasonal-services/{organisation.id}/{service.id}/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == service.id
    assert payload["licenceNumber"] == licence.number
    assert payload["serviceCode"] == f"{licence.number}/5"
    assert payload["organisationName"] == organisation.name


def test_detail_is_404_for_missing_or_foreign_service(org_context):
    client, organisation, _licence, _user = org_context
    foreign = SeasonalServiceFactory()

    assert (
        client.get(f"/api/seasonal-services/{organisation.id}/999999/").status_code
        == 404
    )
    assert (
        client.get(
            f"/api/seasonal-services/{organisation.id}/{foreign.id}/"
        ).status_code
        == 404
    )


def test_update_changes_only_dates(org_context):
    client, organisation, licence, _user = org_context
    service = SeasonalServiceFactory(licence=licence, registration_code=5)

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/{service.id}/update/",
        start=FUTURE_START.isoformat(),
        end=FUTURE_END.isoformat(),
        registrationCode=999,
    )

    assert response.status_code == 200
    service.refresh_from_db()
    assert service.start == FUTURE_START
    assert service.end == FUTURE_END
    assert service.registration_code == 5


def test_update_returns_validation_errors(org_context):
    client, organisation, licence, _user = org_context
    service = SeasonalServiceFactory(licence=licence)

    past = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/{service.id}/update/",
        start="2020-01-01",
        end="2020-02-01",
    )
    reversed_dates = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/{service.id}/update/",
        start=FUTURE_END.isoformat(),
        end=FUTURE_START.isoformat(),
    )

    assert past.status_code == 400
    assert past.json()["field_errors"] == {"end": ["End date cannot be in the past"]}
    assert reversed_dates.status_code == 400
    assert reversed_dates.json()["field_errors"] == {
        "end": ["Start date must be earlier than end date"]
    }


def test_update_is_404_for_foreign_service(org_context):
    client, organisation, _licence, _user = org_context
    foreign = SeasonalServiceFactory()

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/{foreign.id}/update/",
        start=FUTURE_START.isoformat(),
        end=FUTURE_END.isoformat(),
    )

    assert response.status_code == 404


def test_delete_removes_service_and_clamps_page(org_context):
    client, organisation, licence, _user = org_context
    services = [
        SeasonalServiceFactory(
            licence=licence,
            registration_code=index,
            end=datetime.date(2023, 2, 1) + datetime.timedelta(days=index),
            start=datetime.date(2023, 1, 1),
        )
        for index in range(11)
    ]

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/delete/",
        id=services[-1].id,
        page=2,
    )

    assert response.status_code == 200
    assert response.json() == {"deleted": True, "page": 1}
    assert not SeasonalService.objects.filter(id=services[-1].id).exists()
    assert SeasonalService.objects.count() == 10


def test_delete_does_not_remove_another_organisations_service(org_context):
    client, organisation, _licence, _user = org_context
    foreign = SeasonalServiceFactory()

    response = _post(
        client,
        f"/api/seasonal-services/{organisation.id}/delete/",
        id=foreign.id,
    )

    assert response.status_code == 200
    assert SeasonalService.objects.filter(id=foreign.id).exists()


def test_delete_requires_an_id(org_context):
    client, organisation, _licence, _user = org_context

    response = _post(client, f"/api/seasonal-services/{organisation.id}/delete/")

    assert response.status_code == 400
    assert "id" in response.json()["field_errors"]


def test_methods_are_restricted(org_context):
    client, organisation, _licence, _user = org_context

    assert client.post(f"/api/seasonal-services/{organisation.id}/").status_code == 405
    assert (
        client.get(f"/api/seasonal-services/{organisation.id}/delete/").status_code
        == 405
    )
