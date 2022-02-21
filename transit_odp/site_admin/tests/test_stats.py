from unittest.mock import Mock, patch

import factory
import pytest
from django.contrib.auth import get_user_model
from requests.exceptions import RequestException

from transit_odp.organisation.constants import (
    AVLType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.factories import (
    DatasetFactory,
    DraftDatasetFactory,
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models import Organisation
from transit_odp.site_admin.stats import (
    get_active_dataset_counts,
    get_operator_count,
    get_orgs_with_active_dataset_counts,
    get_service_code_counts,
    get_siri_vm_vehicle_counts,
    get_user_counts,
)
from transit_odp.users.factories import (
    AgentUserFactory,
    OrgAdminFactory,
    OrgStaffFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db
User = get_user_model()

ExpiredStatus = FeedStatus.expired.value
InactiveStatus = FeedStatus.inactive.value
LiveStatus = FeedStatus.live.value


def test_organisation_count():
    # active orgs created as a side effect of creating admin users
    active_org_count = 4
    OrgAdminFactory.create_batch(active_org_count)

    admin = OrgAdminFactory()
    inactive_org = admin.organisations.first()
    inactive_org.is_active = False
    inactive_org.save()

    operator_count = get_operator_count()

    assert operator_count == active_org_count

    active_org = Organisation.objects.filter(is_active=True).first()
    active_org.is_active = False
    active_org.save()
    operator_count = get_operator_count()

    assert operator_count == 3


def test_user_counts():
    org_admin_count = 4
    OrgAdminFactory.create_batch(org_admin_count)
    org_staff_count = 5
    OrgStaffFactory.create_batch(org_staff_count)
    OrgStaffFactory.create(is_active=False)
    agent_user_count = 3

    AgentUserFactory.create_batch(agent_user_count)
    inactive_agent_count = 2
    AgentUserFactory.create_batch(inactive_agent_count, is_active=False)

    consumer_count = 3
    UserFactory.create_batch(consumer_count)
    inactive_consumer_count = 2
    UserFactory.create_batch(inactive_consumer_count, is_active=False)

    user_counts = get_user_counts()

    assert user_counts["operator_user_count"] == org_admin_count + org_staff_count
    assert user_counts["agent_user_count"] == agent_user_count
    assert user_counts["consumer_count"] == consumer_count


def test_user_counts_when_org_is_deactivated():
    org = OrganisationFactory()
    OrgAdminFactory(organisations=(org,))
    OrgStaffFactory(organisations=(org,))

    operator_count = get_operator_count()
    user_counts = get_user_counts()

    assert operator_count == 1
    assert user_counts["operator_user_count"] == 2
    assert user_counts["agent_user_count"] == 0
    assert user_counts["consumer_count"] == 0

    org.is_active = False
    org.save()

    operator_count = get_operator_count()
    user_counts = get_user_counts()

    assert operator_count == 0
    assert user_counts["operator_user_count"] == 0
    assert user_counts["agent_user_count"] == 0
    assert user_counts["consumer_count"] == 0


def test_active_dataset_count():
    active_timetable_count = 3
    DatasetFactory.create_batch(active_timetable_count, dataset_type=TimetableType)
    draft_timetable_count = 2
    DraftDatasetFactory.create_batch(draft_timetable_count, dataset_type=TimetableType)
    expired_timetable_count = 1
    DatasetFactory.create_batch(
        expired_timetable_count,
        dataset_type=TimetableType,
        live_revision__status=ExpiredStatus,
    )

    active_avl_count = 2
    DatasetFactory.create_batch(active_avl_count, dataset_type=AVLType)
    draft_avl_count = 4
    DraftDatasetFactory.create_batch(draft_avl_count, dataset_type=AVLType)
    DatasetFactory.create_batch(
        2,
        dataset_type=AVLType,
        live_revision__status=InactiveStatus,
    )

    active_fares_count = 4
    DatasetFactory.create_batch(active_fares_count, dataset_type=FaresType)
    draft_fares_count = 1
    DraftDatasetFactory.create_batch(draft_fares_count, dataset_type=FaresType)
    DatasetFactory.create_batch(
        3, dataset_type=FaresType, live_revision__status=ExpiredStatus
    )

    dataset_counts = get_active_dataset_counts()

    assert dataset_counts["timetables_count"] == active_timetable_count
    assert dataset_counts["avl_count"] == active_avl_count
    assert dataset_counts["fares_count"] == active_fares_count


def test_active_dataset_inactive_org():
    org = OrganisationFactory()
    DatasetFactory(organisation=org, dataset_type=TimetableType)
    DatasetFactory(organisation=org, dataset_type=AVLType)
    DatasetFactory(organisation=org, dataset_type=FaresType)

    dataset_counts = get_active_dataset_counts()
    assert dataset_counts["timetables_count"] == 1
    assert dataset_counts["avl_count"] == 1
    assert dataset_counts["fares_count"] == 1

    org.is_active = False
    org.save()

    dataset_counts = get_active_dataset_counts()
    assert dataset_counts["timetables_count"] == 0
    assert dataset_counts["avl_count"] == 0
    assert dataset_counts["fares_count"] == 0


def test_published_operator_count():
    org1, org2, org3 = [OrganisationFactory() for _ in range(3)]

    # 2 orgs with timetables published
    DatasetFactory(organisation=org1, dataset_type=TimetableType)
    DatasetFactory.create_batch(3, organisation=org2, dataset_type=TimetableType)

    # 1 org with avl published
    DatasetFactory.create_batch(2, organisation=org3, dataset_type=AVLType)

    # 2 orgs with fares published
    DatasetFactory.create_batch(3, organisation=org1, dataset_type=FaresType)
    DatasetFactory(organisation=org3, dataset_type=FaresType)

    counts = get_orgs_with_active_dataset_counts()

    assert counts["published_timetable_operator_count"] == 2
    assert counts["published_avl_operator_count"] == 1
    assert counts["published_fares_operator_count"] == 2

    org1.is_active = False
    org1.save()

    counts = get_orgs_with_active_dataset_counts()

    assert counts["published_timetable_operator_count"] == 1
    assert counts["published_avl_operator_count"] == 1
    assert counts["published_fares_operator_count"] == 1


def test_service_code_counts_multiple_statuses():
    """
    GIVEN 6 timetable datasets: 3 with registered service codes and statuses
    expired, inactive, and live; and 3 with unregistered service codes and statuses
    expired, inactive, and live
    WHEN `get_service_code_counts` is called
    THEN the returned dictionary will contain a value of 1 for
    `registered_service_code_count` and a value of 1 for
    `unregistered_service_code_count`.
    """
    org = OrganisationFactory()
    statuses = (
        FeedStatus.expired.value,
        FeedStatus.inactive.value,
        FeedStatus.live.value,
    )
    service_code_gen = factory.Sequence(lambda n: f"SC000123:{n}")
    attr_count = 3
    TXCFileAttributesFactory.create_batch(
        attr_count,
        service_code=service_code_gen,
        revision__status=factory.Iterator(statuses),
        revision__dataset__dataset_type=TimetableType,
        revision__dataset__organisation=org,
    )

    service_code_gen = factory.Sequence(lambda n: f"UZ000123:{n}")
    TXCFileAttributesFactory.create_batch(
        attr_count,
        service_code=service_code_gen,
        revision__status=factory.Iterator(statuses),
        revision__dataset__dataset_type=TimetableType,
        revision__dataset__organisation=org,
    )

    counts = get_service_code_counts()
    assert counts["registered_service_code_count"] == 1
    assert counts["unregistered_service_code_count"] == 1


def test_service_code_counts_live_revisions():
    """
    GIVEN 6 timetable datasets, 2 with live revisions and registered service codes,
    2 with live revisions and unregistered service codes, 1 with a registered service
    code and no live revision and 1 with an unregistered service code and no live
    revision
    WHEN `get_service_code_counts` is called
    THEN the returned dictionary will contain a value of 2 for
    `registered_service_code_count` and a value of 2 for
    `unregistered_service_code_count`.
    """
    org = OrganisationFactory()
    service_code_gen = factory.Sequence(lambda n: f"SC000123:{n}")
    attr_count = 2
    TXCFileAttributesFactory.create_batch(
        attr_count,
        service_code=service_code_gen,
        revision__dataset__dataset_type=TimetableType,
        revision__dataset__organisation=org,
    )
    dataset = DraftDatasetFactory(dataset_type=TimetableType, organisation=org)
    TXCFileAttributesFactory(
        service_code=service_code_gen, revision=dataset.revisions.last()
    )

    service_code_gen = factory.Sequence(lambda n: f"UZ000123:{n}")
    TXCFileAttributesFactory.create_batch(
        attr_count,
        service_code=service_code_gen,
        revision__dataset__dataset_type=TimetableType,
        revision__dataset__organisation=org,
    )
    dataset = DraftDatasetFactory(dataset_type=TimetableType, organisation=org)
    TXCFileAttributesFactory(
        service_code=service_code_gen, revision=dataset.revisions.last()
    )

    counts = get_service_code_counts()
    assert counts["registered_service_code_count"] == 2
    assert counts["unregistered_service_code_count"] == 2


def test_service_code_counts_inactive_org():
    """
    GIVEN 6 timetable datasets, 3 with registered service codes and 3 with
    unregistered service codes, in an inactive organisation
    WHEN `get_service_code_counts` is called
    THEN the returned dictionary will contain a value of 0 for
    `registered_service_code_count` and a value of 0 for
    `unregistered_service_code_count`.
    """
    org = OrganisationFactory(is_active=False)
    service_code_gen = factory.Sequence(lambda n: f"SC000123:{n}")
    attr_count = 3
    TXCFileAttributesFactory.create_batch(
        attr_count,
        service_code=service_code_gen,
        revision__dataset__dataset_type=TimetableType,
        revision__dataset__organisation=org,
    )

    service_code_gen = factory.Sequence(lambda n: f"UZ000123:{n}")
    TXCFileAttributesFactory.create_batch(
        attr_count,
        service_code=service_code_gen,
        revision__dataset__dataset_type=TimetableType,
        revision__dataset__organisation=org,
    )

    counts = get_service_code_counts()
    assert counts["registered_service_code_count"] == 0
    assert counts["unregistered_service_code_count"] == 0


def test_get_siri_vm_vehicle_counts():
    """
    Given that the CAVL stats API returns vehicle counts
    When I call get_siri_vm_vehicle_counts
    Then I should get back the number of siri vm vehicles
    """
    with patch("transit_odp.site_admin.stats.requests") as requests:
        response = Mock(status_code=200)
        expected_siri_vm_count = 18561
        response.json.return_value = {
            "num_of_gtfs_rt_vehicles": 18692,
            "num_of_siri_vehicles": expected_siri_vm_count,
            "query_time": 0.023499011993408203,
            "version": "0.8.3",
        }
        requests.get.return_value = response
        result = get_siri_vm_vehicle_counts()
        assert result == expected_siri_vm_count


def test_get_siri_vm_vehicle_counts_exceptions():
    """
    Given that the CAVL stats API returns an exception
    When I call get_siri_vm_vehicle_counts
    Then I should get back 0
    """
    with patch("transit_odp.site_admin.stats.requests") as requests:
        requests.get.side_effect = RequestException
        result = get_siri_vm_vehicle_counts()
        assert result == 0
