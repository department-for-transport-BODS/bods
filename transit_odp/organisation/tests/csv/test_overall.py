import datetime

import pandas as pd
import pytest
from waffle import flag_is_active

from django.utils.timezone import now

from transit_odp.organisation.csv.overall import _get_overall_catalogue_dataframe
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.fares.factories import (
    DataCatalogueMetaDataFactory
)
pytestmark = pytest.mark.django_db
is_fares_validator_active = flag_is_active("", "is_fares_validator_active")


def test_df_contains_correct_number_of_rows():
    past = datetime.datetime(2020, 12, 25)
    current = now()
    timetable = DatasetRevisionFactory(published_at=current)
    TXCFileAttributesFactory(revision=timetable, service_code="PD000001")
    AVLDatasetRevisionFactory(published_at=past, dataset__avl_feed_last_checked=current)
    if is_fares_validator_active:
        orgs = OrganisationFactory.create_batch(3)
        DataCatalogueMetaDataFactory(
                fares_metadata__revision__dataset__organisation=orgs[0],
                fares_metadata__revision__is_published=True,
            )
        FaresDatasetRevisionFactory(published_at=current)
        df = _get_overall_catalogue_dataframe()
        assert len(df) == 5
    else:
        df = _get_overall_catalogue_dataframe()
        assert len(df) == 2


def test_df_timetables_expected():
    current = now()
    org = OrganisationFactory(nocs=["test1", "test2", "test3"])
    timetable = DatasetRevisionFactory(published_at=current, dataset__organisation=org)
    fa = TXCFileAttributesFactory(revision=timetable, service_code="PD000001")
    DataCatalogueMetaDataFactory(
            fares_metadata__revision__dataset__organisation=org,
            fares_metadata__revision__is_published=True,
        )
    FaresDatasetRevisionFactory(published_at=current)
    df = _get_overall_catalogue_dataframe()
    row = df.iloc[0]
    assert row["Operator"] == org.name
    assert row["Operator ID"] == org.id
    assert row["Data Type"] == "Timetables"
    assert row["Profile NOCs"] == "test1; test2; test3"
    assert row["Status"] == "published"
    assert row["Last Updated"] == pd.Timestamp(current)
    assert row["File Name"] == timetable.upload_file
    assert row["Data Set/Feed Name"] == timetable.name
    assert row["Data ID"] == timetable.dataset.id
    assert row["Mode"] == "Bus"
    assert row["National Operator Code"] == fa.national_operator_code
    assert row["Service Code"] == fa.service_code
    assert row["Line Name"] == "line1 line2"
    if is_fares_validator_active:
        assert row["XML File Name"] == fa.filename
    else:
        assert row["TXC File Name"] == fa.filename


def test_df_avls_expected():
    current = now()
    past = datetime.datetime(2020, 12, 25)
    org = OrganisationFactory(nocs=["test1", "test2", "test3"])
    avl = AVLDatasetRevisionFactory(
        published_at=past,
        dataset__avl_feed_last_checked=current,
        dataset__organisation=org,
    )
    TXCFileAttributesFactory(service_code="PD000001")
    # need a random TxC FA entry so txc df isnt empty. This will only be empty on
    # new installs
    DataCatalogueMetaDataFactory(
            fares_metadata__revision__dataset__organisation=org,
            fares_metadata__revision__is_published=True,
        )
    FaresDatasetRevisionFactory(published_at=current)
    df = _get_overall_catalogue_dataframe()
    row = df.iloc[0]
    assert row["Operator"] == org.name
    assert row["Operator ID"] == org.id
    assert row["Data Type"] == "Automatic Vehicle Locations"
    assert row["Profile NOCs"] == "test1; test2; test3"
    assert row["Status"] == "published"
    assert row["Last Updated"] == pd.Timestamp(current)
    assert row["Data Set/Feed Name"] == avl.name
    assert row["Data ID"] == avl.dataset_id
    assert row["Mode"] == "Bus"


def test_df_fares_expected():
    current = now()
    org = OrganisationFactory(nocs=["test1", "test2", "test3"])
    fare = FaresDatasetRevisionFactory(
        published_at=current,
        dataset__organisation=org,
    )
    TXCFileAttributesFactory(service_code="PD000001")
    # need a random TxC FA entry so txc df isnt empty. This will only be empty on
    # new installs
    if is_fares_validator_active:
        DataCatalogueMetaDataFactory(
                fares_metadata__revision__dataset__organisation=org,
                fares_metadata__revision__is_published=True,
            )
    df = _get_overall_catalogue_dataframe()
    row = df.iloc[0]
    assert row["Operator"] == org.name
    assert row["Operator ID"] == org.id
    assert row["Data Type"] == "Fares"
    assert row["Profile NOCs"] == "test1; test2; test3"
    assert row["Status"] == "published"
    assert row["Last Updated"] == pd.Timestamp(current)
    assert row["File Name"] == fare.upload_file
    assert row["Data Set/Feed Name"] == fare.name
    assert row["Data ID"] == fare.dataset_id
    assert row["Mode"] == "Bus"
