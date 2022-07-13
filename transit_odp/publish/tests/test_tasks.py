import csv
import io
from datetime import datetime
from zipfile import ZipFile

import pytest
from freezegun import freeze_time

from transit_odp.organisation.csv.consumer_interactions import CSV_HEADERS
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.organisation.models import ConsumerStats
from transit_odp.organisation.tests.csv.test_consumer_interactions import (
    setup_test_data,
)
from transit_odp.publish.constants import INTERACTIONS_DEFINITION
from transit_odp.publish.tasks import (
    task_generate_consumer_interaction_stats,
    task_generate_monthly_consumer_interaction_breakdowns,
)

pytestmark = pytest.mark.django_db


def test_csv_is_generated_and_zipped():
    no_of_datasets = 3
    time_period = 30
    org = setup_test_data(no_of_datasets, time_period)
    now = datetime.now()
    expected_base = f"Consumer_metrics_{org.name}_{now:%d%m%y}"
    expected_zip = expected_base + ".zip"
    expected_csv = expected_base + ".csv"
    expected_namelist = [expected_csv, INTERACTIONS_DEFINITION]
    with freeze_time(now):
        task_generate_monthly_consumer_interaction_breakdowns()

    org.stats.refresh_from_db()
    breakdown = org.stats.monthly_breakdown
    with breakdown.open("rb") as f:
        assert f.name == expected_zip
        with ZipFile(f, "r") as zf:
            assert zf.namelist() == expected_namelist
            with zf.open(expected_csv, "r") as breakdown_csv:
                rows = list(csv.reader(io.TextIOWrapper(breakdown_csv, "utf-8")))
                assert rows[0] == CSV_HEADERS


def test_zip_is_only_added_to_organsations_with_active_datasets():
    bad_org_ids = [org.id for org in OrganisationFactory.create_batch(5)]
    good_org_ids = [setup_test_data().id for _ in range(3)]

    task_generate_monthly_consumer_interaction_breakdowns()
    assert (
        ConsumerStats.objects.filter(
            organisation_id__in=bad_org_ids, monthly_breakdown=""
        ).count()
        == 5
    )
    assert (
        ConsumerStats.objects.filter(
            organisation_id__in=good_org_ids, monthly_breakdown=""
        ).count()
        == 0
    )


def test_organisation_stats_are_generated():
    no_of_datasets = 3
    days_of_requests = 7
    with freeze_time(datetime.now()):
        # See setup_test_data to see constants
        org = setup_test_data(3, 7)
        task_generate_consumer_interaction_stats()
    org.stats.refresh_from_db()

    # API HITS
    list_all_datasets = 6
    no_of_list_all_requests = 1
    direct_datasets = no_of_datasets * 3
    no_of_direct_requests = 3
    assert org.stats.weekly_api_hits == (
        (list_all_datasets * no_of_list_all_requests * days_of_requests)
        + (direct_datasets * no_of_direct_requests * days_of_requests)
    )

    # Downloads
    list_all_datasets = 6
    no_of_list_all_requests = 2
    direct_datasets = no_of_datasets * 3
    no_of_direct_requests = 4
    # AVL doesnt have a direct download feature
    absent_avl_downloads = 3 * no_of_direct_requests * days_of_requests

    assert org.stats.weekly_downloads == (
        (list_all_datasets * no_of_list_all_requests * days_of_requests)
        + (direct_datasets * no_of_direct_requests * days_of_requests)
        - (absent_avl_downloads)
    )
    assert org.stats.weekly_unique_consumers == 1
