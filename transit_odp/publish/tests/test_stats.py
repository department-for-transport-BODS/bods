import pytest

from config.hosts import DATA_HOST
from transit_odp.common.utils import reverse_path
from transit_odp.organisation.csv.consumer_interactions import (
    filter_interactions_to_organisation,
)
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.publish.stats import get_all_consumer_interaction_stats
from transit_odp.site_admin.factories import (
    APIRequestFactory,
    ResourceRequestCounterFactory,
)
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_timetables_api_hits():
    no_of_datasets = 10
    no_of_list_requests = 10
    no_of_direct_requests = 3
    org = OrganisationFactory()
    revisions = [
        DatasetRevisionFactory(is_published=True, dataset__organisation=org).dataset_id
        for _ in range(no_of_datasets)
    ]
    APIRequestFactory.create_batch(
        no_of_list_requests, path_info=reverse_path("api:feed-list", host=DATA_HOST)
    )
    for id_ in revisions[2:-2]:
        APIRequestFactory.create_batch(
            no_of_direct_requests,
            path_info=reverse_path(
                "api:feed-detail",
                kwargs={"pk": id_},
                host=DATA_HOST,
            ),
        )

    df = get_all_consumer_interaction_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["api_direct_hits_total"] == 6 * no_of_direct_requests
    assert row["api_list_hits_total"] == no_of_list_requests * no_of_datasets
    assert row["direct_downloads_total"] == 0
    assert row["bulk_downloads_total"] == 0


def test_avl_api_hits():
    no_of_datasets = 10
    no_of_list_requests = 10
    no_of_direct_requests = 3
    org = OrganisationFactory()
    revisions = [
        AVLDatasetRevisionFactory(
            is_published=True, dataset__organisation=org
        ).dataset_id
        for _ in range(no_of_datasets)
    ]
    APIRequestFactory.create_batch(
        no_of_list_requests // 2,
        path_info=reverse_path("api:avldatafeedapi", host=DATA_HOST),
    )
    APIRequestFactory.create_batch(
        no_of_list_requests // 2,
        path_info=reverse_path("api:gtfsrtdatafeedapi", host=DATA_HOST),
    )
    for id_ in revisions[2:-2]:
        APIRequestFactory.create_batch(
            no_of_direct_requests,
            path_info=reverse_path(
                "api:avldetaildatafeedapi",
                kwargs={"pk": id_},
                host=DATA_HOST,
            ),
        )

    df = get_all_consumer_interaction_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["api_direct_hits_total"] == 6 * no_of_direct_requests
    assert row["api_list_hits_total"] == no_of_list_requests * no_of_datasets
    assert row["direct_downloads_total"] == 0
    assert row["bulk_downloads_total"] == 0


def test_fares_api_hits():
    no_of_datasets = 10
    no_of_list_requests = 10
    no_of_direct_requests = 3
    org = OrganisationFactory()
    revisions = [
        FaresDatasetRevisionFactory(
            is_published=True, dataset__organisation=org
        ).dataset_id
        for _ in range(no_of_datasets)
    ]
    APIRequestFactory.create_batch(
        no_of_list_requests,
        path_info=reverse_path("api:fares-api-list", host=DATA_HOST),
    )
    for id_ in revisions[2:-2]:
        APIRequestFactory.create_batch(
            no_of_direct_requests,
            path_info=reverse_path(
                "api:fares-api-detail",
                kwargs={"pk": id_},
                host=DATA_HOST,
            ),
        )

    df = get_all_consumer_interaction_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["api_direct_hits_total"] == 6 * no_of_direct_requests
    assert row["api_list_hits_total"] == no_of_list_requests * no_of_datasets
    assert row["direct_downloads_total"] == 0
    assert row["bulk_downloads_total"] == 0


def test_total_timetable_downloads():
    no_of_datasets = 10
    no_of_bulk_downloads = 10
    no_of_direct_downloads = 3
    org = OrganisationFactory()
    revisions = [
        DatasetRevisionFactory(is_published=True, dataset__organisation=org).dataset_id
        for _ in range(no_of_datasets)
    ]
    ResourceRequestCounterFactory.create_batch(
        no_of_bulk_downloads, path_info=reverse_path("downloads-bulk", host=DATA_HOST)
    )
    for id_ in revisions[2:-2]:
        ResourceRequestCounterFactory.create_batch(
            no_of_direct_downloads,
            path_info=reverse_path(
                "feed-download",
                kwargs={"pk": id_},
                host=DATA_HOST,
            ),
        )
    df = get_all_consumer_interaction_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["direct_downloads_total"] == 6 * no_of_direct_downloads
    assert row["bulk_downloads_total"] == no_of_datasets * no_of_bulk_downloads
    assert row["api_direct_hits_total"] == 0
    assert row["api_list_hits_total"] == 0


def test_total_avl_downloads():
    no_of_datasets = 10
    no_of_bulk_downloads = 10
    org = OrganisationFactory()

    AVLDatasetRevisionFactory.create_batch(
        no_of_datasets, is_published=True, dataset__organisation=org
    )

    ResourceRequestCounterFactory.create_batch(
        no_of_bulk_downloads,
        path_info=reverse_path("downloads-avl-bulk", host=DATA_HOST),
    )
    df = get_all_consumer_interaction_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["bulk_downloads_total"] == no_of_datasets * no_of_bulk_downloads
    assert row["direct_downloads_total"] == 0
    assert row["api_direct_hits_total"] == 0
    assert row["api_list_hits_total"] == 0


def test_total_fares_downloads():
    no_of_datasets = 10
    no_of_bulk_downloads = 10
    no_of_direct_downloads = 3
    org = OrganisationFactory()
    revisions = [
        FaresDatasetRevisionFactory(
            is_published=True, dataset__organisation=org
        ).dataset_id
        for _ in range(no_of_datasets)
    ]
    ResourceRequestCounterFactory.create_batch(
        no_of_bulk_downloads,
        path_info=reverse_path("downloads-fares-bulk", host=DATA_HOST),
    )
    for id_ in revisions[2:-2]:
        ResourceRequestCounterFactory.create_batch(
            no_of_direct_downloads,
            path_info=reverse_path(
                "fares-feed-download",
                kwargs={"pk": id_},
                host=DATA_HOST,
            ),
        )
    df = get_all_consumer_interaction_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["direct_downloads_total"] == 6 * no_of_direct_downloads
    assert row["bulk_downloads_total"] == no_of_bulk_downloads * no_of_datasets
    assert row["api_direct_hits_total"] == 0
    assert row["api_list_hits_total"] == 0


def test_unique_user_count_with_unique_users():
    no_of_datasets = 10
    no_of_list_requests = 10
    no_of_direct_requests = 3
    org = OrganisationFactory()
    revisions = [
        DatasetRevisionFactory(is_published=True, dataset__organisation=org).dataset_id
        for _ in range(no_of_datasets)
    ]
    APIRequestFactory.create_batch(
        no_of_list_requests, path_info=reverse_path("api:feed-list", host=DATA_HOST)
    )
    for id_ in revisions[2:-2]:
        APIRequestFactory.create_batch(
            no_of_direct_requests,
            path_info=reverse_path(
                "api:feed-detail",
                kwargs={"pk": id_},
                host=DATA_HOST,
            ),
        )
    df = get_all_consumer_interaction_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 1
    row = df.iloc[0]
    # The factory will create a new user for each request so the no of unique users
    # is the same as the number of total requests
    assert row["unique_users"] == 6 * no_of_direct_requests + no_of_list_requests


def test_unique_user_count_with_single_user():
    no_of_datasets = 10
    no_of_list_requests = 10
    no_of_direct_requests = 3
    user = UserFactory()
    org = OrganisationFactory()
    revisions = [
        DatasetRevisionFactory(is_published=True, dataset__organisation=org).dataset_id
        for _ in range(no_of_datasets)
    ]
    APIRequestFactory.create_batch(
        no_of_list_requests,
        path_info=reverse_path("api:feed-list", host=DATA_HOST),
        requestor=user,
    )
    for id_ in revisions[2:-2]:
        APIRequestFactory.create_batch(
            no_of_direct_requests,
            path_info=reverse_path(
                "api:feed-detail",
                kwargs={"pk": id_},
                host=DATA_HOST,
            ),
            requestor=user,
        )
    df = get_all_consumer_interaction_stats()
    df = filter_interactions_to_organisation(df, org.id)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["unique_users"] == 1  # the user defined at the top


def test_no_datasets_api():
    assert len(get_all_consumer_interaction_stats()) == 0


def test_no_datasets_downloads():
    assert len(get_all_consumer_interaction_stats()) == 0


def test_no_datasets_unique_users():
    assert len(get_all_consumer_interaction_stats()) == 0
