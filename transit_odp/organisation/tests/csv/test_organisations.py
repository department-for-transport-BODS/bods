from datetime import datetime, timedelta

import factory
import pytest
from freezegun import freeze_time
from waffle import flag_is_active

from transit_odp.data_quality.factories import PTIValidationResultFactory
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.fares_validator.factories import FaresValidationResultFactory
from transit_odp.organisation.constants import ORG_ACTIVE
from transit_odp.organisation.csv.organisation import (
    _get_organisation_catalogue_dataframe,
)
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
    LicenceFactory,
    OperatorCodeFactory,
    OrganisationFactory,
    ServiceCodeExemptionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.otc.constants import SCHOOL_OR_WORKS, SubsidiesDescription
from transit_odp.otc.factories import LicenceModelFactory, ServiceModelFactory
from transit_odp.users.constants import OrgAdminType
from transit_odp.users.factories import InvitationFactory, OrgAdminFactory

pytestmark = pytest.mark.django_db


@freeze_time("25-12-2021")
def test_df_organisations():
    """
    GIVEN: An Organisation has published various datasets that have services
    registered in OTC AND have licence defined that are also in OTC
    WHEN: We generate the organisation_data_catalogue.csv
    THEN: The data in the csv should reflect this
    """
    is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
    registered_service_count = 3
    unregistered_service_count = 2
    valid_operating_service_count = 3
    future_operating_services_count = 2
    no_of_licences = 3
    published_exempted_service_codes_count = 2
    published_otc_services = 5
    unpublished_otc_services = 3
    unpublished_exempted_Service_codes_count = unpublished_otc_services
    total_exempted_service_codes_count = (
        published_exempted_service_codes_count
        + unpublished_exempted_Service_codes_count
    )
    total_otc_services = published_otc_services + unpublished_otc_services
    services_registered_in_scope = (
        total_otc_services - total_exempted_service_codes_count
    )
    compliant_reg_services_ratio = (
        f"{published_otc_services / services_registered_in_scope * 100:.2f}%"
    )
    no_of_fares_products = 10
    avl_revisions = 2
    no_of_revisions = 14
    no_of_compliant_fares = 5
    no_of_percentage_fares_compliance = (
        f"{no_of_compliant_fares / no_of_revisions * 100:.2f}%"
    )
    no_of_pass_products = 2
    no_of_trip_products = 3

    now = datetime.now()
    today = now.date()
    before = today - timedelta(days=2)
    after = today + timedelta(days=2)
    organisation = OrganisationFactory(
        licence_required=True, nocs=["test1", "test2", "test3"]
    )
    licences = LicenceFactory.create_batch(no_of_licences, organisation=organisation)
    OrgAdminFactory.create_batch(5, organisations=(organisation,), last_login=now)
    InvitationFactory(organisation=organisation, account_type=OrgAdminType, sent=now)
    timetable_revision = DatasetRevisionFactory(dataset__organisation=organisation)
    AVLDatasetRevisionFactory.create_batch(
        avl_revisions, dataset__organisation=organisation
    )
    fares_revision = FaresDatasetRevisionFactory(dataset__organisation=organisation)
    FaresMetadataFactory(
        revision=fares_revision, num_of_fare_products=no_of_fares_products
    )
    FaresValidationResultFactory(revision=fares_revision, count=no_of_fares_products)
    TXCFileAttributesFactory.create_batch(
        unregistered_service_count,
        revision=timetable_revision,
        service_code=factory.Sequence(lambda n: f"UZ0000{n:03}:{n}"),
        operating_period_start_date=before,
        operating_period_end_date=before,
    )
    TXCFileAttributesFactory.create_batch(
        registered_service_count,
        revision=timetable_revision,
        service_code=factory.Sequence(lambda n: f"RE0000{n:03}:{n}"),
        operating_period_start_date=before,
        operating_period_end_date=before,
    )

    TXCFileAttributesFactory.create_batch(
        valid_operating_service_count,
        revision=timetable_revision,
        operating_period_start_date=before,
        operating_period_end_date=after,
        service_code=factory.Sequence(lambda n: f"VA0000{n:03}:{n}"),
    )
    # "Valid" operating dates, note VA for valid!
    TXCFileAttributesFactory.create_batch(
        future_operating_services_count,
        revision=timetable_revision,
        operating_period_start_date=after,
        service_code=factory.Sequence(lambda n: f"FT0000{n:03}:{n}"),
    )
    # "Future" start, note FT for future!

    org_licences = [lic.number for lic in licences]
    otc_licences = [LicenceModelFactory(number=lic) for lic in org_licences]

    for idx, licence in enumerate(otc_licences + otc_licences[:2]):
        # registered services in BODS
        service = ServiceModelFactory(
            licence=licence,
            service_type_description=SCHOOL_OR_WORKS,
            subsidies_description=SubsidiesDescription.NO,
            registration_code=factory.sequence(lambda n: n + 100),
        )
        TXCFileAttributesFactory(
            licence_number=service.licence.number,
            service_code=service.registration_number.replace("/", ":"),
            revision=timetable_revision,
        )
        if idx < published_exempted_service_codes_count:
            org_licence = next(lic for lic in licences if lic.number == licence.number)
            ServiceCodeExemptionFactory(
                licence=org_licence, registration_code=service.registration_code
            )

    # registered services not in BODS
    not_published_sc = ServiceModelFactory.create_batch(
        unpublished_otc_services,
        licence=otc_licences[2],
        registration_code=factory.sequence(lambda n: n + 100),
    )
    for x in not_published_sc:
        org_licence = next(lic for lic in licences if lic.number == x.licence.number)
        ServiceCodeExemptionFactory(
            licence=org_licence, registration_code=x.registration_code
        )

    # makes all service compliant
    PTIValidationResultFactory(revision=timetable_revision, count=0)
    expected_licence_string = ";".join(org_licences)

    df = _get_organisation_catalogue_dataframe()
    row = df.iloc[0]
    assert row["Name"] == organisation.name
    assert row["Status"] == ORG_ACTIVE
    assert row["Date Invite Accepted"].isoformat()[:-6] == now.isoformat()
    assert row["Date Invited"].isoformat()[:-6] == now.isoformat()
    assert row["Last Log-In"].isoformat()[:-6] == now.isoformat()
    assert row["Permit Holder"] == "TRUE"
    assert row["National Operator Codes"] == "test1;test2;test3"
    assert row["Licence Numbers"] == expected_licence_string
    assert row["Number of Licences"] == no_of_licences
    assert row["Unregistered Services"] == unregistered_service_count
    assert row["OTC Registered Services"] == total_otc_services
    assert row["Organisation creation date"].isoformat()[:-6] == now.isoformat()
    assert row["Registered Services Published"] == published_otc_services
    assert row["Out of scope services(exempted)"] == total_exempted_service_codes_count
    assert row["Registered Services in scope(for BODS)"] == services_registered_in_scope
    assert row["Compliant Registered Services Published"] == published_otc_services
    assert (
        row["% Compliant Registered Services Published"] == compliant_reg_services_ratio
    )
    assert row["Number of School or Works Services"] == published_otc_services
    assert row["School or Works Services Subsidised"] == 0
    assert row["School or Works Services Subsidised In Part"] == 0
    assert row["Flexible Registration"] == 0
    assert (
        row["Number of Published Services with Valid Operating Dates"]
        == valid_operating_service_count
    )
    assert (
        row["Additional Published Services with Future Start Date"]
        == future_operating_services_count
    )
    assert row["Number of Published Timetable Datasets"] == 1
    assert row["Number of Published AVL Datafeeds"] == avl_revisions
    assert row["Number of Published Fare Datasets"] == 1
    if is_fares_validator_active:
        assert row["Number of Published Fare Datasets"] == no_of_revisions
        assert (
            row["% Compliant Published Fare Datasets"]
            == no_of_percentage_fares_compliance
        )
        assert row["Number of Pass Products"] == no_of_pass_products
        assert row["Number of Trip Products"] == no_of_trip_products
    else:
        assert row["Number of Fare Products"] == no_of_fares_products


@pytest.mark.skip
def test_attempt_performance_test():
    # do not unskip this test, it takes ages to generate all the data
    for org in OrganisationFactory.create_batch(
        20,
        licence_required=True,
        name=factory.Sequence(lambda n: f"org{n}"),
    ):
        OperatorCodeFactory.create_batch(3, organisation=org)
        LicenceFactory.create_batch(3, organisation=org)
        user, *_ = OrgAdminFactory.create_batch(
            10,
            organisations=(org,),
            email=factory.sequence(lambda n: f"admin{n}@{org.name}.com"),
        )
        for _ in range(25):
            now = datetime.today()
            before = now - timedelta(days=2)
            after = now + timedelta(days=2)

            timetable_revision = DatasetRevisionFactory(
                dataset__organisation=org, dataset__contact=user
            )
            PTIValidationResultFactory(revision=timetable_revision, count=0)
            TXCFileAttributesFactory.create_batch(
                100,
                revision=timetable_revision,
                operating_period_start_date=before,
                operating_period_end_date=after,
            )
            fares_revision = FaresDatasetRevisionFactory(
                dataset__organisation=org, dataset__contact=user
            )
            FaresMetadataFactory(revision=fares_revision)


def test_df_non_otc_data():
    """
    GIVEN: An organisation doesnt have an licence in OTC
    WHEN: We generate the organisation_data_catalogue.csv
    THEN: The data from the TXCFileAttribute table should still be present in the csv
    """
    registered_service_count = 3
    unregistered_service_count = 2
    valid_operating_service_count = 3
    future_operating_services_count = 2
    unpublished_otc_services = 3
    no_of_fares_products = 10
    avl_revisions = 2

    now = datetime.now()
    today = now.date()
    before = today - timedelta(days=2)
    after = today + timedelta(days=2)
    organisation = OrganisationFactory(
        licence_required=True, nocs=["test1", "test2", "test3"]
    )
    LicenceFactory(organisation=organisation, number="WX1234567")
    OrgAdminFactory.create_batch(5, organisations=(organisation,), last_login=now)
    InvitationFactory(organisation=organisation, account_type=OrgAdminType, sent=now)
    timetable_revision = DatasetRevisionFactory(dataset__organisation=organisation)
    AVLDatasetRevisionFactory.create_batch(
        avl_revisions, dataset__organisation=organisation
    )
    fares_revision = FaresDatasetRevisionFactory(dataset__organisation=organisation)
    FaresMetadataFactory(
        revision=fares_revision, num_of_fare_products=no_of_fares_products
    )
    TXCFileAttributesFactory.create_batch(
        unregistered_service_count,
        revision=timetable_revision,
        service_code=factory.Sequence(lambda n: f"UZ0000{n:03}:{n}"),
        operating_period_start_date=before,
        operating_period_end_date=before,
    )
    TXCFileAttributesFactory.create_batch(
        registered_service_count,
        revision=timetable_revision,
        service_code=factory.Sequence(lambda n: f"RE0000{n:03}:{n}"),
        operating_period_start_date=before,
        operating_period_end_date=before,
    )

    TXCFileAttributesFactory.create_batch(
        valid_operating_service_count,
        revision=timetable_revision,
        operating_period_start_date=before,
        operating_period_end_date=after,
        service_code=factory.Sequence(lambda n: f"VA0000{n:03}:{n}"),
    )
    TXCFileAttributesFactory.create_batch(
        future_operating_services_count,
        revision=timetable_revision,
        operating_period_start_date=after,
        service_code=factory.Sequence(lambda n: f"FT0000{n:03}:{n}"),
    )

    ServiceModelFactory.create_batch(
        unpublished_otc_services,
        registration_code=factory.sequence(lambda n: n + 100),
    )

    df = _get_organisation_catalogue_dataframe()
    row = df.iloc[0]
    assert row["Name"] == organisation.name
    assert row["Status"] == ORG_ACTIVE
    assert row["Unregistered Services"] == unregistered_service_count
    assert (
        row["Number of Published Services with Valid Operating Dates"]
        == valid_operating_service_count
    )
    assert (
        row["Additional Published Services with Future Start Date"]
        == future_operating_services_count
    )
    assert row["Number of Published Timetable Datasets"] == 1
    assert row["Number of Published AVL Datafeeds"] == avl_revisions
    assert row["Number of Published Fare Datasets"] == 1
    assert row["Number of Fare Products"] == no_of_fares_products


def test_no_licences_or_otc_and_one_dataset():
    """
    GIVEN: An Organisation has published 1 distinct service
    WHEN: We generate the organisation_data_catalogue.csv
    THEN: The TXCFileAttribute stats should be integers and not booleans
    """
    organisation = OrganisationFactory()
    LicenceFactory(number="YZ1234567", organisation=organisation)
    timetable_revision = DatasetRevisionFactory(dataset__organisation=organisation)
    fares_revision = FaresDatasetRevisionFactory(dataset__organisation=organisation)
    FaresMetadataFactory(revision=fares_revision, num_of_fare_products=10)
    TXCFileAttributesFactory(
        revision=timetable_revision,
    )
    ServiceModelFactory.create_batch(
        2,
        registration_code=factory.sequence(lambda n: n + 100),
    )

    df = _get_organisation_catalogue_dataframe()
    row = df.iloc[0]
    assert str(row["Number of Published Services with Valid Operating Dates"]) == "0"


def test_number_of_organisations():
    """
    GIVEN: A known number of organisations have data in BODS
    WHEN: We generate the organisation_data_catalogue.csv
    THEN: The number of organisations should match this, meaning we are not dropping
    any during the generation process
    """
    unregistered_service_count = 2
    unpublished_otc_services = 3
    no_of_fares_products = 10
    avl_revisions = 2

    now = datetime.now()
    today = now.date()
    before = today - timedelta(days=2)
    organisation = OrganisationFactory(
        licence_required=True, nocs=["test1", "test2", "test3"]
    )
    OrganisationFactory.create_batch(3)
    LicenceFactory(number="YZ1234567")
    OrgAdminFactory.create_batch(5, organisations=(organisation,), last_login=now)
    InvitationFactory(organisation=organisation, account_type=OrgAdminType, sent=now)
    timetable_revision = DatasetRevisionFactory(dataset__organisation=organisation)
    AVLDatasetRevisionFactory.create_batch(
        avl_revisions, dataset__organisation=organisation
    )
    fares_revision = FaresDatasetRevisionFactory(dataset__organisation=organisation)
    FaresMetadataFactory(
        revision=fares_revision, num_of_fare_products=no_of_fares_products
    )
    TXCFileAttributesFactory.create_batch(
        unregistered_service_count,
        revision=timetable_revision,
        service_code=factory.Sequence(lambda n: f"UZ0000{n:03}:{n}"),
        operating_period_start_date=before,
        operating_period_end_date=before,
    )
    ServiceModelFactory.create_batch(
        unpublished_otc_services,
        registration_code=factory.sequence(lambda n: n + 100),
    )

    df = _get_organisation_catalogue_dataframe()
    assert len(df) == 5
