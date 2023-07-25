import datetime
from datetime import date

import factory
import pandas as pd
import pytest
from django.utils.timezone import now
from django_hosts import reverse
from waffle import flag_is_active

from config.hosts import PUBLISH_HOST
from transit_odp.avl.factories import PostPublishingCheckReportFactory
from transit_odp.avl.models import PPCReportType
from transit_odp.fares.factories import DataCatalogueMetaDataFactory
from transit_odp.organisation.constants import AVLType
from transit_odp.organisation.csv.overall import _get_overall_catalogue_dataframe
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetFactory,
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
    OrganisationFactory,
    TXCFileAttributesFactory,
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
        # Test for no matching score and no matching report URL for timetables datasets
        assert row["% AVL to Timetables feed matching score"] is None
        assert row["Latest matching report URL"] is None
    else:
        assert row["TXC File Name"] == fa.filename


def test_df_avls_expected():
    today = date.today()
    current = now()
    past = datetime.datetime(2020, 12, 25)
    org = OrganisationFactory(nocs=["test1", "test2", "test3"])
    avl = AVLDatasetRevisionFactory(
        published_at=past,
        dataset__avl_feed_last_checked=current,
        dataset__organisation=org,
    )
    organisation = OrganisationFactory()
    dataset = DatasetFactory(organisation=organisation, dataset_type=AVLType)
    filename = "ppc_weekly_report_test.zip"
    PostPublishingCheckReportFactory(
        dataset=dataset,
        vehicle_activities_analysed=130,
        vehicle_activities_completely_matching=30,
        granularity=PPCReportType.WEEKLY,
        file=factory.django.FileField(filename=filename),
        created=today,
    )
    organisation_two = OrganisationFactory()
    dataset_two = DatasetFactory(organisation=organisation_two, dataset_type=AVLType)
    PostPublishingCheckReportFactory(
        dataset=dataset_two,
        vehicle_activities_analysed=10,
        vehicle_activities_completely_matching=0,
        granularity=PPCReportType.WEEKLY,
        file=factory.django.FileField(filename=filename),
        created=today,
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
    # Test for no matching score, therefore no matching report URL
    assert row["% AVL to Timetables feed matching score"] is None
    assert row["Latest matching report URL"] == ""


def test_df_avls_matching_score_and_report_url():
    organisation = OrganisationFactory()
    today = date.today()
    current = now()
    dataset = DatasetFactory(organisation=organisation, dataset_type=AVLType)
    filename = "ppc_weekly_report_test.zip"
    PostPublishingCheckReportFactory(
        dataset=dataset,
        vehicle_activities_analysed=10,
        vehicle_activities_completely_matching=2,
        granularity=PPCReportType.WEEKLY,
        file=factory.django.FileField(filename=filename),
        created=today,
    )
    TXCFileAttributesFactory(service_code="PD000001")
    DataCatalogueMetaDataFactory(
        fares_metadata__revision__dataset__organisation=organisation,
        fares_metadata__revision__is_published=True,
    )
    FaresDatasetRevisionFactory(published_at=current)

    df = _get_overall_catalogue_dataframe()
    row = df.iloc[0]
    assert row["% AVL to Timetables feed matching score"] == 20.0
    assert row["Latest matching report URL"] == reverse(
        "avl:download-matching-report",
        kwargs={"pk": dataset.id, "pk1": organisation.id},
        host=PUBLISH_HOST,
    )


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
    if is_fares_validator_active:
        # Test for no matching score and no matching report URL for fares datasets
        assert row["% AVL to Timetables feed matching score"] is None
        assert row["Latest matching report URL"] is None
