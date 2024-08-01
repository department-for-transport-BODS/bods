import datetime
from datetime import date

import factory
import pandas as pd
import pytest
from django.utils.timezone import now
from django_hosts import reverse
from waffle.testutils import override_flag

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
is_fares_validator_active = True


@override_flag("is_fares_validator_active", active=True)
@pytest.mark.django_db
def test_df_contains_correct_number_of_rows():
    past = datetime.datetime(2020, 12, 25)
    current = now()
    timetable = DatasetRevisionFactory(published_at=current)
    TXCFileAttributesFactory(revision=timetable, service_code="PD000001")
    AVLDatasetRevisionFactory(published_at=past, dataset__avl_feed_last_checked=current)
    orgs = OrganisationFactory.create_batch(3)
    DataCatalogueMetaDataFactory(
        fares_metadata__revision__dataset__organisation=orgs[0],
        fares_metadata__revision__is_published=True,
    )
    FaresDatasetRevisionFactory(published_at=current)
    df = _get_overall_catalogue_dataframe()
    assert len(df) == 5


@override_flag("is_fares_validator_active", active=True)
@pytest.mark.django_db
def test_df_contains_correct_columns():
    past = datetime.datetime(2020, 12, 25)
    current = now()
    timetable = DatasetRevisionFactory(published_at=current)
    TXCFileAttributesFactory(revision=timetable, service_code="PD000001")
    AVLDatasetRevisionFactory(published_at=past, dataset__avl_feed_last_checked=current)
    orgs = OrganisationFactory.create_batch(3)
    DataCatalogueMetaDataFactory(
        fares_metadata__revision__dataset__organisation=orgs[0],
        fares_metadata__revision__is_published=True,
    )
    FaresDatasetRevisionFactory(published_at=current)
    df = _get_overall_catalogue_dataframe()
    columns = df.columns

    assert columns[0] == "Operator"
    assert columns[1] == "Operator ID"
    assert columns[2] == "Profile NOCs"
    assert columns[3] == "Data Type"
    assert columns[4] == "Status"
    assert columns[5] == "Last Updated"
    assert columns[6] == "File Name"
    assert columns[7] == "XML File Name"
    assert columns[8] == "Data Set/Feed Name"
    assert columns[9] == "Data ID"
    assert columns[10] == "Mode"
    assert columns[11] == "National Operator Code"
    assert columns[12] == "Service Code"
    assert columns[13] == "Line Name"
    assert columns[14] == "Licence Number"
    assert columns[15] == "Public Use Flag"
    assert columns[16] == "Revision Number"
    assert columns[17] == "Operating Period Start Date"
    assert columns[18] == "Operating Period End Date"
    assert columns[19] == "% AVL to Timetables feed matching score"
    assert columns[20] == "Latest matching report URL"


@override_flag("is_fares_validator_active", active=True)
@pytest.mark.django_db
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
    assert row["XML File Name"] == fa.filename
    # Test for no matching score and no matching report URL for timetables datasets
    assert row["% AVL to Timetables feed matching score"] is None
    assert row["Latest matching report URL"] is None


@override_flag("is_fares_validator_active", active=True)
@pytest.mark.django_db
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
    # Test for when no matching score (NaN or None value),
    # therefore there should be no matching report URL.
    assert row["Latest matching report URL"] is None

    second_row = df.iloc[1]
    # Test for when matching score is above 0%,
    # therefore there should be a matching report URL
    assert second_row["% AVL to Timetables feed matching score"] == 23.0
    assert second_row["Latest matching report URL"] == reverse(
        "avl:download-matching-report",
        kwargs={"pk": dataset.id, "pk1": organisation.id},
        host=PUBLISH_HOST,
    )

    third_row = df.iloc[2]
    if is_fares_validator_active:
        # Test for when matching score is 0%,
        # therefore there should be a matching report URL
        assert third_row["% AVL to Timetables feed matching score"] == 0.0
        assert third_row["Latest matching report URL"] == reverse(
            "avl:download-matching-report",
            kwargs={"pk": dataset_two.id, "pk1": organisation_two.id},
            host=PUBLISH_HOST,
        )


@override_flag("is_fares_validator_active", active=True)
@pytest.mark.django_db
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
    assert row["% AVL to Timetables feed matching score"] is None
    assert row["Latest matching report URL"] is None


def test_get_overall_catalogue_dataframe_with_inactive_org():
    active_org = OrganisationFactory(name="active_org", short_name="active_org")
    inactive_org = OrganisationFactory(
        name="inactive_org", short_name="inactive_org", is_active=False
    )
    dataset_1 = DatasetFactory(organisation=active_org)
    dataset_2 = DatasetFactory(organisation=inactive_org)
    dataset_revision_1 = DatasetRevisionFactory(dataset=dataset_1)
    dataset_revision_2 = DatasetRevisionFactory(dataset=dataset_2)
    TXCFileAttributesFactory(revision=dataset_revision_1)
    TXCFileAttributesFactory(revision=dataset_revision_2)
    DataCatalogueMetaDataFactory(
        fares_metadata__revision__dataset__organisation=active_org,
        fares_metadata__revision__is_published=True,
    )
    DataCatalogueMetaDataFactory(
        fares_metadata__revision__dataset__organisation=inactive_org,
        fares_metadata__revision__is_published=True,
    )
    overall_catalogue_df = _get_overall_catalogue_dataframe()
    assert inactive_org.name not in overall_catalogue_df["Operator"].to_list()
