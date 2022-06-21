from collections import OrderedDict
from datetime import datetime

from django.db.models.expressions import F
from pandas import DataFrame, NamedAgg, Series

from transit_odp.common.collections import Column
from transit_odp.fares.models import FaresMetadata
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.organisation.models import Licence, Organisation, TXCFileAttributes
from transit_odp.otc.models import Licence as OTCLicence
from transit_odp.otc.models import Service as OTCService

OTC_SERVICES_FIELDS = ["published_registered_service_count"]
TXC_FIELDS = [
    "organisation_id",
    "service_code",
    "bods_compliant",
    "operating_period_start_date",
    "operating_period_end_date",
]

OTC_LICENCE_FIELDS = [
    "number",
    "distinct_service_count",
    "school_or_work_count",
    "school_or_work_and_subsidies_count",
    "school_or_work_and_in_part_count",
    "flexible_registration_count",
]

ORG_LICENCE_FIELDS = ["number", "organisation_id"]
ORG_FIELDS = [
    "id",
    "name",
    "status",
    "invite_accepted",
    "invite_sent",
    "last_active",
    "permit_holder",
    "nocs_string",
    "licence_string",
    "number_of_licences",
    "published_timetable_count",
    "published_avl_count",
]

ORG_COLUMN_MAP = OrderedDict(
    {
        "name": Column(
            "Name", "The name of the operator/publisher providing data on BODS"
        ),
        "status": Column(
            "Status",
            "The registration status of the operator/publisher on BODS. ‘Active’ "
            "are signed up on BODS, ‘Inactive’ no longer have functioning accounts "
            "on BODS and ‘Pending Invite’ have still haven’t signed up.",
        ),
        "invite_accepted": Column(
            "Date Invite Accepted",
            "The date at which the operator/publisher accepted their "
            "invite and signed up",
        ),
        "invite_sent": Column(
            "Date Invited",
            "The date at which they were originally invited to sign up to BODS",
        ),
        "last_active": Column(
            "Last Log-In",
            "The last time there was activity for the operator/publisher on BODS.",
        ),
        "permit_holder": Column(
            "Permit Holder",
            "The permit status as declared by operator/publisher in the "
            "Organisation profile section on BODS (Permit holder is 'Yes' "
            "if the user clicks the tickbox of 'I don't have a PSV license "
            "number')",
        ),
        "nocs_string": Column(
            "National Operator Codes",
            "The National Operator Codes of the operator/ publisher as declared by "
            "them in the Organisation Profile section on BODS.",
        ),
        "licence_string": Column(
            "Licence Numbers",
            "The Licence number(s) of the operator/publisher as declared "
            "by them in the Organisation Profile section on BODS.",
        ),
        "number_of_licences": Column(
            "Number of Licences",
            "The total count of services of the operator/publisher as declared by them "
            "in the Organisation Profile section on BODS. This informs us "
            "to understand the total number of licence numbers the organisation "
            "is representing.",
        ),
        "unregistered_service_count": Column(
            "Unregistered Services",
            "The total number of unregistered services "
            "(UZ declared in ServiceCode field) are published in total "
            "by the operator/publisher to BODS.",
        ),
        "distinct_service_count": Column(
            "OTC Registered Services",
            (
                "The total count of services of the operator/publisher as "
                "extracted from the database of the Office of the Traffic "
                "Commissioner (OTC). This informs us to understand the total "
                "number of services expected to be published from the licences "
                "associated in the organisational profile."
            ),
        ),
        "published_registered_service_count": Column(
            "Registered Services Published",
            (
                "The total number of registered services that an organisation "
                "has published."
            ),
        ),
        "compliant_service_count": Column(
            "Compliant Registered Services Published",
            (
                "The total number of compliant registered services are "
                "published in total by the operator/publisher to BODS."
            ),
        ),
        "compliant_service_ratio": Column(
            "% Compliant Registered Services Published",
            (
                "The percentage of an organisation’s "
                "registered services that are PTI compliant."
            ),
        ),
        "school_or_work_count": Column(
            "Number of School or Works Services",
            "The total count of school or works services of the operator/publisher as "
            "extracted from the database of the Office of the Traffic Commissioner "
            "(OTC). This informs us to understand the total number of services "
            "expected to be published from the licences associated in the "
            "organisational profile that are 'School or Works'.",
        ),
        "school_or_work_and_subsidies_count": Column(
            "School or Works Services Subsidised",
            "The total count of school or works services that are subsidised for the "
            "operator/publisher as extracted from the database of the Office of the "
            "Traffic Commissioner (OTC). This informs us to understand the total "
            "number of services expected to be published from the licences "
            "associated in the organisational profile that are 'School or Works' "
            "and are fully subsidised (Yes).",
        ),
        "school_or_work_and_in_part_count": Column(
            "School or Works Services Subsidised In Part",
            "The total count of school or works services that are subsidised in "
            "part for the operator/publisher as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC). This informs us to "
            "understand the total number of services expected to be published "
            "from the licences associated in the organisational profile that "
            "are 'School or Works' and are in part subsidised (In Part).",
        ),
        "flexible_registration_count": Column(
            "Flexible Registration",
            "The total count of flexible services for the operator/publisher "
            "as extracted from the database of the Office of the Traffic "
            "Commissioner (OTC). This informs us to understand the total number "
            "of services expected to be published from the licences associated "
            "in the organisational profile that are 'Flexible' services, "
            "so we can prepare organisations for this technical implementation.",
        ),
        "number_of_services_valid_operating_date": Column(
            "Number of Published Services with Valid Operating Dates",
            "The total number of services published on BODS that have a "
            "valid operating period today.",
        ),
        "published_services_with_future_start_date": Column(
            "Additional Published Services with Future Start Date",
            "The total number of additional published services that have "
            "future start dates on BODS. This informs us to understand the "
            "additional number of new services codes that will become valid in "
            "the future, which is just a difference to the total already "
            "provided, to give an indicator to services that are published but "
            "not valid now.",
        ),
        "published_timetable_count": Column(
            "Number of Published Timetable Datasets",
            "The total number of published timetables datasets provided "
            "by the operator/publisher to BODS.",
        ),
        "published_avl_count": Column(
            "Number of Published AVL Datafeeds",
            "The total number of published location data feeds provided "
            "by the operator/publisher to BODS.",
        ),
        "published_fares_count": Column(
            "Number of Published Fare Datasets",
            "The total number of published fares datasets provided "
            "by the operator/publisher to BODS.",
        ),
        "total_fare_products": Column(
            "Number of Fare Products",
            "The total number of fares products found in the fares data provided "
            "by the operator/publisher to BODS.",
        ),
    }
)


def _get_compliance_percentage(row: Series) -> str:
    percentage = 0.0
    if row.published_registered_service_count:
        percentage = (
            row.compliant_service_count / row.published_registered_service_count
        )
    return f"{percentage * 100:.2f}%"


def _get_fares_dataframe() -> DataFrame:
    fares = FaresMetadata.objects.filter(
        revision__dataset__live_revision=F("revision_id"), revision__status="live"
    ).annotate(organisation_id=F("revision__dataset__organisation_id"))
    columns = ("revision_id", "organisation_id", "num_of_fare_products")
    df = DataFrame.from_records(fares.values(*columns))
    df = df.groupby("organisation_id").agg(
        {"revision_id": ["count"], "num_of_fare_products": ["sum"]}
    )
    if df is not None:
        df = df.droplevel(axis=1, level=0)
        df = df.rename(
            columns={
                "count": "published_fares_count",
                "sum": "total_fare_products",
            }
        )
    else:
        raise EmptyDataFrame()

    return df


def _is_valid_operating_date(row: Series) -> bool:
    today = datetime.now().date()
    if row.operating_period_end_date is None or row.operating_period_start_date is None:
        return False
    return row.operating_period_start_date <= today <= row.operating_period_end_date


def _get_service_stats() -> DataFrame:
    today = datetime.now().date()
    SERVICE_CODE = "service_code"
    otc_services = DataFrame.from_records(
        OTCService.objects.add_service_code().values(SERVICE_CODE)
    )
    if otc_services.empty:
        raise EmptyDataFrame()

    otc_services["is_registered"] = True
    txc_files = DataFrame.from_records(
        TXCFileAttributes.objects.get_organisation_data_catalogue().values(*TXC_FIELDS)
    )
    txc_files["unregistered_service_count"] = txc_files["service_code"].str.startswith(
        "UZ"
    )
    txc_files["number_of_services_valid_operating_date"] = txc_files.apply(
        lambda x: _is_valid_operating_date(x), axis=1
    )
    txc_files["published_services_with_future_start_date"] = (
        txc_files["operating_period_start_date"] > today
    )

    merged_services = otc_services.merge(txc_files, on=SERVICE_CODE, how="outer")
    merged_services["is_registered_and_compliant"] = (
        merged_services["is_registered"] & merged_services["bods_compliant"]
    )
    service_code_count = (
        merged_services.groupby("organisation_id")
        .agg(
            published_registered_service_count=NamedAgg(
                column="is_registered", aggfunc="sum"
            ),
            compliant_service_count=NamedAgg(
                column="is_registered_and_compliant", aggfunc="sum"
            ),
            unregistered_service_count=NamedAgg(
                column="unregistered_service_count", aggfunc="sum"
            ),
            number_of_services_valid_operating_date=NamedAgg(
                column="number_of_services_valid_operating_date", aggfunc="sum"
            ),
            published_services_with_future_start_date=NamedAgg(
                column="published_services_with_future_start_date", aggfunc="sum"
            ),
        )
        .astype(int)
    )

    if service_code_count is not None:
        service_code_count["compliant_service_ratio"] = service_code_count.apply(
            lambda x: _get_compliance_percentage(x), axis=1
        )
        return service_code_count
    else:
        raise EmptyDataFrame()


def _get_organisation_catalogue_dataframe() -> DataFrame:
    otc_licences = DataFrame.from_records(
        OTCLicence.objects.add_data_annotations().values(*OTC_LICENCE_FIELDS)
    )
    org_licences = DataFrame.from_records(Licence.objects.values(*ORG_LICENCE_FIELDS))
    orgs = DataFrame.from_records(
        Organisation.objects.add_data_catalogue_fields().values(*ORG_FIELDS)
    )

    if otc_licences.empty or orgs.empty or org_licences.empty:
        raise EmptyDataFrame()

    service_stats = _get_service_stats()
    orgs = orgs.merge(
        service_stats, how="left", left_on="id", right_on="organisation_id"
    )

    licences = org_licences.merge(otc_licences, how="left", on="number")
    licences = licences.groupby("organisation_id").sum()

    orgs = orgs.merge(licences, how="outer", left_on="id", right_on="organisation_id")
    fares = _get_fares_dataframe()
    orgs = orgs.merge(fares, how="outer", left_on="id", right_on="organisation_id")

    pti_columns = ["compliant_service_count", "compliant_service_ratio"]
    fares_columns = ["published_fares_count", "total_fare_products"]
    # we don't need to fill 'number' in OTC_LICENCE_FIELDS
    otc_columns = OTC_LICENCE_FIELDS[1:] + OTC_SERVICES_FIELDS

    fillna_columns = otc_columns + pti_columns + fares_columns
    orgs[fillna_columns] = orgs[fillna_columns].fillna(0)

    drop_columns = ["id"]
    orgs.drop(columns=drop_columns, inplace=True)
    rename_map = {
        old_name: column_tuple.field_name
        for old_name, column_tuple in ORG_COLUMN_MAP.items()
    }
    orgs = orgs[ORG_COLUMN_MAP.keys()].rename(columns=rename_map)
    return orgs


def get_organisation_catalogue_csv() -> str:
    return _get_organisation_catalogue_dataframe().to_csv(index=False)
