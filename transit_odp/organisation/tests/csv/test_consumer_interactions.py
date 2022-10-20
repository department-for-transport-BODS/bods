from datetime import datetime, timedelta

import factory
import pandas as pd
import pytest

from transit_odp.organisation.csv.consumer_interactions import (
    API_LIST_URLS,
    BULK_DOWNLOAD_URLS,
    filter_interactions_to_organisation,
    get_all_monthly_breakdown_stats,
)
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetFactory,
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import Dataset
from transit_odp.site_admin.factories import (
    APIRequestFactory,
    ResourceRequestCounterFactory,
)
from transit_odp.users.constants import OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def setup_test_data(no_of_datasets=3, time_period=30):
    """
    Loads everything!:
    each type of dataset over a known time period
    some have subscriptions, most will not
    some will be called directly in both api and download
    some will never be called directly
    """
    admin = UserFactory(account_type=OrgAdminType)
    org = OrganisationFactory(
        key_contact=admin, name=factory.Sequence(lambda n: f"test_company{n}")
    )
    consumer = UserFactory()
    now = datetime.now()
    DatasetRevisionFactory.create_batch(
        no_of_datasets,
        dataset__contact=admin,
        dataset__subscribers=[consumer],
        dataset__organisation=org,
    )
    FaresDatasetRevisionFactory.create_batch(
        no_of_datasets, dataset__contact=admin, dataset__organisation=org
    )
    AVLDatasetRevisionFactory.create_batch(
        no_of_datasets, dataset__contact=admin, dataset__organisation=org
    )
    DatasetRevisionFactory.create_batch(
        no_of_datasets, dataset__contact=admin, dataset__organisation=org
    )

    datasets = (
        Dataset.objects.add_dataset_download_url().add_api_url().order_by("id")[:9]
    )
    for time in range(time_period):
        time = now - timedelta(time)
        APIRequestFactory(
            created=time,
            path_info=API_LIST_URLS[0],
            requestor=consumer,
        )
        ResourceRequestCounterFactory(
            date=time.date(),
            path_info=BULK_DOWNLOAD_URLS[0],
            counter=2,
            requestor=consumer,
        )
        for dataset in datasets:
            APIRequestFactory.create_batch(
                3,
                created=time,
                path_info=dataset.api_detail_url,
                requestor=consumer,
            )
            if dataset.dataset_download_url:
                ResourceRequestCounterFactory(
                    date=time.date(),
                    path_info=dataset.dataset_download_url,
                    counter=4,
                    requestor=consumer,
                )

    return org


def test_empty_dataframes_doesnt_raise():
    OrganisationFactory()
    get_all_monthly_breakdown_stats()


def test_empty_api_hits_returns_only_direct():
    bulk_downloads = 1
    direct_downloads = 2
    no_of_datasets = 3

    admin = UserFactory(account_type=OrgAdminType)
    org = OrganisationFactory(key_contact=admin)
    consumer = UserFactory()
    now = datetime.now()
    DatasetRevisionFactory.create_batch(
        no_of_datasets,
        dataset__contact=admin,
        dataset__subscribers=[consumer],
        dataset__organisation=org,
    )
    ResourceRequestCounterFactory(
        date=now.date(),
        path_info=BULK_DOWNLOAD_URLS[0],
        counter=bulk_downloads,
        requestor=consumer,
    )
    datasets = Dataset.objects.add_dataset_download_url().add_api_url()
    for dataset in datasets:
        ResourceRequestCounterFactory(
            date=now.date(),
            path_info=dataset.dataset_download_url,
            counter=direct_downloads,
            requestor=consumer,
        )

    df = get_all_monthly_breakdown_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == no_of_datasets
    assert pd.Series.all(df["total_api_hits"] == 0)
    assert pd.Series.all(df["bulk_downloads"] == bulk_downloads)
    assert pd.Series.all(df["direct_downloads"] == direct_downloads)
    assert pd.Series.all(df["dataset_type_pretty"] == "Timetables")


def test_empty_direct_returns_only_api_hits():
    api_hits = 1
    api_list_hits = 2
    no_of_datasets = 3

    admin = UserFactory(account_type=OrgAdminType)
    org = OrganisationFactory(key_contact=admin)
    consumer = UserFactory()
    now = datetime.now()
    DatasetRevisionFactory.create_batch(
        no_of_datasets,
        dataset__contact=admin,
        dataset__subscribers=[consumer],
        dataset__organisation=org,
    )
    APIRequestFactory.create_batch(
        api_list_hits,
        created=now,
        path_info=API_LIST_URLS[0],
        requestor=consumer,
    )
    datasets = Dataset.objects.add_dataset_download_url().add_api_url()
    for dataset in datasets:
        APIRequestFactory.create_batch(
            api_hits,
            created=now,
            path_info=dataset.api_detail_url,
            requestor=consumer,
        )

    df = get_all_monthly_breakdown_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == no_of_datasets
    assert pd.Series.all(df["total_api_hits"] == api_list_hits + api_hits)
    assert pd.Series.all(df["bulk_downloads"] == 0)
    assert pd.Series.all(df["direct_downloads"] == 0)
    assert pd.Series.all(df["dataset_type_pretty"] == "Timetables")


def test_only_bulk_downloads():
    admin = UserFactory(account_type=OrgAdminType)
    org = OrganisationFactory(key_contact=admin)
    consumer = UserFactory()
    now = datetime.now()
    revision = DatasetRevisionFactory(
        dataset__contact=admin,
        dataset__subscribers=[consumer],
        dataset__organisation=org,
    )
    ResourceRequestCounterFactory(
        date=now.date(),
        path_info=BULK_DOWNLOAD_URLS[0],
        counter=1,
        requestor=consumer,
    )
    ResourceRequestCounterFactory(
        date=now.date() - timedelta(days=1),
        path_info=BULK_DOWNLOAD_URLS[0],
        counter=1,
        requestor=consumer,
    )
    df = get_all_monthly_breakdown_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 2, "same dataset over two days"

    assert pd.Series.all(df["total_api_hits"] == 0)
    assert pd.Series.all(df["bulk_downloads"] == 1)
    assert pd.Series.all(df["direct_downloads"] == 0)
    assert pd.Series.all(df["dataset_type_pretty"] == "Timetables")
    assert pd.Series.all(df["dataset_id"] == revision.dataset.id)


def test_only_bulk_gtfs_downloads():
    admin = UserFactory(account_type=OrgAdminType)
    org = OrganisationFactory(key_contact=admin)
    consumer = UserFactory()
    now = datetime.now()
    revision = DatasetRevisionFactory(
        dataset__contact=admin,
        dataset__subscribers=[consumer],
        dataset__organisation=org,
    )
    ResourceRequestCounterFactory(
        date=now.date(),
        path_info=BULK_DOWNLOAD_URLS[1],
        counter=1,
        requestor=consumer,
    )
    ResourceRequestCounterFactory(
        date=now.date() - timedelta(days=1),
        path_info=BULK_DOWNLOAD_URLS[1],
        counter=1,
        requestor=consumer,
    )
    df = get_all_monthly_breakdown_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 2

    assert pd.Series.all(df["bulk_downloads"] == 1)
    assert pd.Series.all(df["direct_downloads"] == 0)
    assert pd.Series.all(df["dataset_type_pretty"] == "Timetables")
    assert pd.Series.all(df["dataset_id"] == revision.dataset.id)


def test_only_api_hits():
    admin = UserFactory(account_type=OrgAdminType)
    org = OrganisationFactory(key_contact=admin)
    consumer = UserFactory()
    now = datetime.now()
    revision = DatasetRevisionFactory(
        dataset__contact=admin,
        dataset__subscribers=[consumer],
        dataset__organisation=org,
    )
    APIRequestFactory(
        created=now,
        path_info=API_LIST_URLS[0],
        requestor=consumer,
    )
    APIRequestFactory(
        created=now - timedelta(days=1),
        path_info=API_LIST_URLS[0],
        requestor=consumer,
    )
    dataset = Dataset.objects.add_dataset_download_url().add_api_url().first()
    APIRequestFactory(
        created=now,
        path_info=dataset.api_detail_url,
        requestor=consumer,
    )
    APIRequestFactory(
        created=now - timedelta(days=1),
        path_info=dataset.api_detail_url,
        requestor=consumer,
    )
    df = get_all_monthly_breakdown_stats()
    df = filter_interactions_to_organisation(df, org.id)

    assert len(df) == 2, "same dataset over two days"

    assert pd.Series.all(df["total_api_hits"] == 2)
    assert pd.Series.all(df["bulk_downloads"] == 0)
    assert pd.Series.all(df["direct_downloads"] == 0)
    assert pd.Series.all(df["dataset_type_pretty"] == "Timetables")
    assert pd.Series.all(df["dataset_id"] == revision.dataset.id)


def test_only_direct_downloads():
    admin = UserFactory(account_type=OrgAdminType)
    org = OrganisationFactory(key_contact=admin)
    consumer = UserFactory()
    now = datetime.now()
    revision = DatasetRevisionFactory(
        dataset__contact=admin,
        dataset__subscribers=[consumer],
        dataset__organisation=org,
    )
    dataset = Dataset.objects.add_dataset_download_url().add_api_url().first()
    ResourceRequestCounterFactory(
        date=now.date(),
        path_info=dataset.dataset_download_url,
        counter=1,
        requestor=consumer,
    )
    ResourceRequestCounterFactory(
        date=now.date() - timedelta(days=1),
        path_info=dataset.dataset_download_url,
        counter=1,
        requestor=consumer,
    )
    df = get_all_monthly_breakdown_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 2, "same dataset over two days"

    assert pd.Series.all(df["total_api_hits"] == 0)
    assert pd.Series.all(df["bulk_downloads"] == 0)
    assert pd.Series.all(df["direct_downloads"] == 1)
    assert pd.Series.all(df["dataset_type_pretty"] == "Timetables")
    assert pd.Series.all(df["dataset_id"] == revision.dataset.id)


def test_get_all_consumer_interactions_df():
    no_of_datasets = 3
    time_period = 30
    org = setup_test_data(no_of_datasets, time_period)
    df = get_all_monthly_breakdown_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 4 * no_of_datasets * time_period


def test_datasets_from_other_organisations_are_filtered_out():
    DatasetFactory.create_batch(5)
    admin = UserFactory(account_type=OrgAdminType)
    org = OrganisationFactory(key_contact=admin)
    consumer = UserFactory()
    now = datetime.now()
    revision = DatasetRevisionFactory(
        dataset__contact=admin,
        dataset__subscribers=[consumer],
        dataset__organisation=org,
    )
    ResourceRequestCounterFactory(
        date=now.date(),
        path_info=BULK_DOWNLOAD_URLS[0],
        counter=1,
        requestor=consumer,
    )
    dataset = (
        Dataset.objects.add_dataset_download_url()
        .add_api_url()
        .get(id=revision.dataset_id)
    )
    ResourceRequestCounterFactory(
        date=now.date(),
        path_info=dataset.dataset_download_url,
        counter=1,
        requestor=consumer,
    )

    df = get_all_monthly_breakdown_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 1
    assert pd.Series.all(df["dataset_id"] == revision.dataset_id)
