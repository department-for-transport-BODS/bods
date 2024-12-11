from datetime import date, timedelta

import pytest
from django.utils.timezone import now
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    DraftDatasetFactory,
)
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.organisation.factories import (
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.otc.factories import (
    LicenceModelFactory,
    LocalAuthorityFactory,
    ServiceModelFactory,
    UILtaFactory,
)
from transit_odp.users.constants import OrgStaffType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_avl_require_attention_stats(publish_client):
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))

    total_services = 7
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n:03}" for n in range(total_services)]
    all_line_names = [f"line:{n}" for n in range(total_services)]
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    # add NOC to all TXC
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
        line_names=[all_line_names[0]],
    )
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
        line_names=[all_line_names[1]],
    )
    dataset2 = DraftDatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(),
        service_code=all_service_codes[2],
        line_names=[all_line_names[2]],
    )
    live_revision = DatasetRevisionFactory(dataset=dataset2)
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=all_service_codes[3],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
        line_names=[all_line_names[3]],
    )
    otc_lic1 = LicenceModelFactory(number=licence_number)
    services = []
    for index, code in enumerate(all_service_codes):
        services.append(
            ServiceModelFactory(
                licence=otc_lic1,
                registration_number=code.replace(":", "/"),
                service_number=all_line_names[index],
            )
        )

    ui_lta = UILtaFactory(name="UI_LTA")
    LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    publish_client.force_login(user=user)
    url = reverse("avl:requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": ""}, follow=True)

    assert response.status_code == 200
    assert len(response.context["view"].object_list) == 7
    assert response.context["total_in_scope_in_season_services"] == 7
    assert response.context["services_require_attention_percentage"] == 100


def test_avl_require_attention_search_no_results(publish_client):
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))

    total_services = 3
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n:03}" for n in range(total_services)]
    all_line_names = [f"line:{n}" for n in range(total_services)]
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
        line_names=[all_line_names[0]],
    )
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
        line_names=[all_line_names[1]],
    )
    otc_lic1 = LicenceModelFactory(number=licence_number)
    services = []
    for index, code in enumerate(all_service_codes):
        services.append(
            ServiceModelFactory(
                licence=otc_lic1,
                registration_number=code.replace(":", "/"),
                service_number=all_line_names[index],
            )
        )

    ui_lta = UILtaFactory(name="UI_LTA")
    LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    publish_client.force_login(user=user)
    url = reverse("avl:requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": "test123"}, follow=True)

    assert response.status_code == 200
    assert len(response.context["table"].data) == 0


def test_avl_require_attention_search_results(publish_client):
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))

    total_services = 7
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n:03}" for n in range(total_services)]
    all_line_names = [f"line:{n}" for n in range(total_services)]
    print("all_service_codes>>", all_service_codes)
    print("all_line_names>>", all_line_names)
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
        line_names=[all_line_names[0]],
    )
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
        line_names=[all_line_names[1]],
    )
    dataset2 = DraftDatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(),
        service_code=all_service_codes[2],
        line_names=[all_line_names[2]],
    )
    live_revision = DatasetRevisionFactory(dataset=dataset2)
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=all_service_codes[3],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
        line_names=[all_line_names[3]],
    )
    otc_lic1 = LicenceModelFactory(number=licence_number)
    services = []
    for index, code in enumerate(all_service_codes):
        services.append(
            ServiceModelFactory(
                licence=otc_lic1,
                registration_number=code.replace(":", "/"),
                service_number=all_line_names[index],
            )
        )

    ui_lta = UILtaFactory(name="UI_LTA")
    LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    publish_client.force_login(user=user)
    url = reverse("avl:requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": "PD5000229"}, follow=True)

    assert response.status_code == 200
    assert len(response.context["table"].data) == 7
