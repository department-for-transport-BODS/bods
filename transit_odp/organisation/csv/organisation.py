from collections import OrderedDict
from datetime import datetime

import pandas as pd
from django.db.models.expressions import F
from django_hosts import reverse
from pandas import DataFrame, NamedAgg, Series, isna, merge
from waffle import flag_is_active

from config.hosts import PUBLISH_HOST
from transit_odp.common.collections import Column
from transit_odp.fares.models import FaresMetadata
from transit_odp.fares_validator.models import FaresValidationResult
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.organisation.models import Licence, Organisation, TXCFileAttributes
from transit_odp.organisation.models.data import ServiceCodeExemption
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
ORG_DATASET_FIELDS = [
    "id",
    "published_timetable_count",
    "published_avl_count",
]
ORG_USER_FIELDS = [
    "id",
    "invite_accepted",
    "invite_sent",
    "last_active",
    "status",
]
ORG_FIELDS = [
    "id",
    "name",
    "created",
    "permit_holder",
    "nocs_string",
    "licence_string",
    "number_of_licences",
    "operator_avl_to_timtables_matching_score",
]

FEATURE_FLAG_ORG_COLUMN_MAP = OrderedDict(
    {
        "name": Column(
            "Name", "The name of the operator/publisher providing data on BODS"
        ),
        "status": Column(
            "Status",
            "The registration status of the operator/publisher on BODS. 'Active' "
            "are signed up on BODS, 'Inactive' no longer have functioning accounts "
            "on BODS, 'Pending Invite' still haven't signed up and 'Not yet invited' "
            "have been added to BODS but not yet invited to complete the full sign "
            "up procedure",
        ),
        "invite_accepted": Column(
            "Date Invite Accepted",
            "The date at which the operator/publisher accepted their "
            "invite and signed up",
        ),
        "created": Column(
            "Organisation creation date",
            "The date at which the Operator/publisher organisation are added to "
            "BODS which may or may not be the same date as the invited date.",
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
            "The total count of services of the operator/publisher as "
            "extracted from the database of the Office of the Traffic "
            "Commissioner (OTC). This informs us to understand the total "
            "number of services expected to be published from the licences "
            "associated in the organisational profile.",
        ),
        "exempted_services_count": Column(
            "Out of scope services(exempted)",
            "The total number of registered services that have been marked as "
            "exempt from publishing to BODS by the DVSA/DfT admin user.",
        ),
        "services_registered_in_bods_count": Column(
            "Registered Services in scope(for BODS)",
            "The total number of in scope, registered services for the "
            "organisation that require data in BODS",
        ),
        "published_registered_service_count": Column(
            "Registered Services Published",
            "The total number of registered services that an organisation "
            "has published.",
        ),
        "compliant_service_count": Column(
            "Compliant Registered Services Published",
            "The total number of compliant, in scope, registered services "
            "are published in total by the operator/publisher to BODS.",
        ),
        "compliant_service_ratio": Column(
            "% Compliant Registered Services Published",
            "The percentage of an organisation's in scope, "
            "registered services that are PTI compliant.",
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
        "number_of_revisions_count": Column(
            "Number of Published Fare Datasets",
            (
                "The total number of published fares datasets "
                "provided by the operator/publisher to BODS."
            ),
        ),
        "compliant_fares_count": Column(
            "% Compliant Published Fare Datasets",
            (
                "The percentage of an organisation's published "
                "fare datasets that are BODS compliant."
            ),
        ),
        "num_of_pass_products_count": Column(
            "Number of Pass Products",
            (
                "The total number of pass products as extracted from "
                "the files provided by the operator/publisher to BODS."
            ),
        ),
        "num_of_trip_products_count": Column(
            "Number of Trip Products",
            (
                "The total number of trip limited products as extracted "
                "from the files provided by the operator/publisher to BODS."
            ),
        ),
        "operator_avl_to_timtables_matching_score": Column(
            "% Operator overall AVL to Timetables matching score",
            (
                "The overall score for an operator as per ‘Review my "
                "location data’ blue dashboard for an operator."
            ),
        ),
        "archived_matching_report_url": Column(
            "Archived matching reports URL",
            (
                "The same archived reports url as the ‘Review my location "
                "data’ blue dashboard for an operator in Download all "
                "archived matching reports."
            ),
        ),
    }
)
ORG_COLUMN_MAP = OrderedDict(
    {
        "name": Column(
            "Name", "The name of the operator/publisher providing data on BODS"
        ),
        "status": Column(
            "Status",
            "The registration status of the operator/publisher on BODS. 'Active' "
            "are signed up on BODS, 'Inactive' no longer have functioning accounts "
            "on BODS, 'Pending Invite' still haven't signed up and 'Not yet invited' "
            "have been added to BODS but not yet invited to complete the full sign "
            "up procedure",
        ),
        "invite_accepted": Column(
            "Date Invite Accepted",
            "The date at which the operator/publisher accepted their "
            "invite and signed up",
        ),
        "created": Column(
            "Organisation creation date",
            "The date at which the Operator/publisher organisation are added to "
            "BODS which may or may not be the same date as the invited date.",
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
            "The total count of services of the operator/publisher as "
            "extracted from the database of the Office of the Traffic "
            "Commissioner (OTC). This informs us to understand the total "
            "number of services expected to be published from the licences "
            "associated in the organisational profile.",
        ),
        "exempted_services_count": Column(
            "Out of scope services(exempted)",
            "The total number of registered services that have been marked as "
            "exempt from publishing to BODS by the DVSA/DfT admin user.",
        ),
        "services_registered_in_bods_count": Column(
            "Registered Services in scope(for BODS)",
            "The total number of in scope, registered services for the "
            "organisation that require data in BODS",
        ),
        "published_registered_service_count": Column(
            "Registered Services Published",
            "The total number of registered services that an organisation "
            "has published.",
        ),
        "compliant_service_count": Column(
            "Compliant Registered Services Published",
            "The total number of compliant, in scope, registered services "
            "are published in total by the operator/publisher to BODS.",
        ),
        "compliant_service_ratio": Column(
            "% Compliant Registered Services Published",
            "The percentage of an organisation's in scope, "
            "registered services that are PTI compliant.",
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
    if (
        isna(row.services_registered_in_bods_count)
        or isna(row.compliant_service_count)
        or not row.services_registered_in_bods_count
    ):
        return str(percentage)

    percentage = row.compliant_service_count / row.services_registered_in_bods_count
    return f"{percentage * 100:.2f}%"


def _get_fares_compliance_percentage(row: Series) -> str:
    percentage = 0.0
    if (
        isna(row.number_of_revisions_count)
        or isna(row.compliant_fares_count)
        or not row.number_of_revisions_count
    ):
        return f"{percentage * 100:.2f}%"

    percentage = row.compliant_fares_count / row.number_of_revisions_count
    return f"{percentage * 100:.2f}%"


def _get_services_registered_in_bods(row: Series) -> int:
    if row.distinct_service_count:
        if isna(row.exempted_services_count):
            return row.distinct_service_count
        else:
            return row.distinct_service_count - row.exempted_services_count
    return 0


def _get_fares_dataframe() -> DataFrame:
    is_fares_validator_active = flag_is_active("", "is_fares_validator_active")

    fares = FaresMetadata.objects.filter(
        revision__dataset__live_revision=F("revision_id"), revision__status="live"
    ).annotate(organisation_id=F("revision__dataset__organisation_id"))

    if not is_fares_validator_active:
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
    else:
        columns = (
            "revision_id",
            "organisation_id",
            "num_of_pass_products",
            "num_of_trip_products",
        )
        fares_df = DataFrame.from_records(fares.values(*columns))

        fares_columns = ("organisation_id", "revision_id", "count")
        compliance = FaresValidationResult.objects.filter(
            revision__dataset__live_revision=F("revision_id"), revision__status="live"
        )

        compliance_status_df = DataFrame.from_records(compliance.values(*fares_columns))
        if not compliance_status_df.empty:
            compliance_status_df.query("count == 0", inplace=True)
            compliance_count_df = compliance_status_df.groupby(
                ["organisation_id"], as_index=False
            )["count"].count()
            compliance_count_df.columns = ["organisation_id", "compliant_fares_count"]
        else:
            raise EmptyDataFrame

        if not fares_df.empty:
            fares_count_df = fares_df.groupby("organisation_id").agg(
                {
                    "revision_id": ["count"],
                    "num_of_pass_products": ["count"],
                    "num_of_trip_products": ["count"],
                }
            )
            fares_count_df.columns = [
                "number_of_revisions_count",
                "num_of_pass_products_count",
                "num_of_trip_products_count",
            ]
        else:
            raise EmptyDataFrame

        merged = merge(
            fares_count_df,
            compliance_count_df,
            left_on="organisation_id",
            right_on="organisation_id",
            how="outer",
        )
        if merged.empty:
            raise EmptyDataFrame()
        return merged


def _is_valid_operating_date(row: Series) -> bool:
    if not row.is_published:
        return False

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

    exempted_services = DataFrame.from_records(
        ServiceCodeExemption.objects.add_service_code()
        .add_organisation_id()
        .values("service_code", "org_id"),
        columns=["service_code", "org_id"],
    )

    otc_services["is_registered"] = True
    txc_files = DataFrame.from_records(
        TXCFileAttributes.objects.get_organisation_data_catalogue().values(*TXC_FIELDS)
    )
    merged_services = otc_services.merge(txc_files, on=SERVICE_CODE, how="outer")

    merged_services["is_published"] = merged_services["organisation_id"].notna()
    merged_services["is_registered_and_published"] = (
        merged_services["is_registered"] & merged_services["is_published"]
    )
    merged_services["is_registered_and_compliant"] = (
        merged_services["is_registered"] & merged_services["bods_compliant"]
    )

    merged_services["unregistered_service_count"] = merged_services[
        "service_code"
    ].str.startswith("UZ")
    merged_services["number_of_services_valid_operating_date"] = merged_services.apply(
        lambda x: _is_valid_operating_date(x), axis=1
    )
    merged_services["published_services_with_future_start_date"] = (
        merged_services["operating_period_start_date"] > today
    ) & merged_services["is_published"]
    merged_services["is_exempted"] = merged_services["service_code"].isin(
        exempted_services["service_code"]
    )

    # Initially organisation_id column can have NaN values inside.
    # We override it here with org_id for entries with exempted service codes
    # to be able to properly sum all exempted service codes in .agg(..) method.
    merged_services = merged_services.merge(
        exempted_services, on=SERVICE_CODE, how="outer"
    )
    merged_services.organisation_id.fillna(merged_services["org_id"], inplace=True)
    del merged_services["org_id"]

    service_code_count = (
        merged_services.groupby(["organisation_id"])
        .agg(
            published_registered_service_count=NamedAgg(
                column="is_registered_and_published", aggfunc="sum"
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
            exempted_services_count=NamedAgg(column="is_exempted", aggfunc="sum"),
        )
        .astype(int)
    )

    if service_code_count is None:
        raise EmptyDataFrame()

    return service_code_count


def _get_archived_matching_report_url(row: Series) -> str:
    if row["operator_avl_to_timtables_matching_score"] is None or pd.isna(
        row["operator_avl_to_timtables_matching_score"]
    ):
        return None
    if row["operator_avl_to_timtables_matching_score"] is not None:
        return reverse(
            "ppc-archive",
            kwargs={"pk1": row["id"]},
            host=PUBLISH_HOST,
        )


def _get_organisation_details_dataframe() -> DataFrame:
    orgs = DataFrame.from_records(
        Organisation.objects.values("id", "name")
        .add_nocs_string(delimiter=";")
        .add_licence_string(delimiter=";")
        .add_number_of_licences()
        .add_permit_holder()
        .add_avl_stats()
        .values(*ORG_FIELDS)
    )

    if orgs.empty:
        raise EmptyDataFrame

    orgs_with_datasets = DataFrame.from_records(
        Organisation.objects.values("id")
        .add_live_published_dataset_count_types()
        .values(*ORG_DATASET_FIELDS)
    )
    orgs_with_users = DataFrame.from_records(
        Organisation.objects.values("id")
        .add_status()
        .add_invite_accepted()
        .add_invite_sent()
        .add_last_active()
        .values(*ORG_USER_FIELDS)
    )

    orgs = orgs.merge(orgs_with_datasets, on="id")
    orgs = orgs.merge(orgs_with_users, on="id")
    return orgs


def _prepare_calculated_columns(df: DataFrame) -> None:
    is_fares_validator_active = flag_is_active("", "is_fares_validator_active")

    df["services_registered_in_bods_count"] = df.apply(
        lambda x: _get_services_registered_in_bods(x), axis=1
    )
    df["compliant_service_ratio"] = df.apply(
        lambda x: _get_compliance_percentage(x), axis=1
    )
    if is_fares_validator_active:
        df["archived_matching_report_url"] = df.apply(
            lambda x: _get_archived_matching_report_url(x), axis=1
        )
        df["compliant_fares_count"] = df.apply(
            lambda x: _get_fares_compliance_percentage(x), axis=1
        )


def _populate_nan_with_zeros(df: DataFrame):
    pti_columns = ["compliant_service_count", "compliant_service_ratio"]
    is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
    if is_fares_validator_active:
        fares_columns = [
            "num_of_pass_products_count",
            "num_of_trip_products_count",
            "compliant_fares_count",
        ]
    else:
        fares_columns = ["published_fares_count", "total_fare_products"]
    # we don't need to fill 'number' in OTC_LICENCE_FIELDS
    otc_columns = OTC_LICENCE_FIELDS[1:] + OTC_SERVICES_FIELDS
    services_columns = ["services_registered_in_bods_count", "exempted_services_count"]

    fillna_columns = otc_columns + pti_columns + fares_columns + services_columns
    df[fillna_columns] = df[fillna_columns].fillna(0)


def _get_organisation_catalogue_dataframe() -> DataFrame:
    otc_licences = DataFrame.from_records(
        OTCLicence.objects.add_data_annotations().values(*OTC_LICENCE_FIELDS)
    )
    org_licences = DataFrame.from_records(Licence.objects.values(*ORG_LICENCE_FIELDS))
    orgs = _get_organisation_details_dataframe()

    if otc_licences.empty or orgs.empty or org_licences.empty:
        raise EmptyDataFrame()

    licences = org_licences.merge(otc_licences, how="left", on="number")
    licences = licences.groupby("organisation_id").sum()
    orgs = orgs.merge(licences, how="outer", left_on="id", right_on="organisation_id")

    fares = _get_fares_dataframe()
    orgs = orgs.merge(fares, how="outer", left_on="id", right_on="organisation_id")

    service_stats = _get_service_stats()
    orgs = orgs.merge(
        service_stats, how="left", left_on="id", right_on="organisation_id"
    )

    _prepare_calculated_columns(orgs)
    _populate_nan_with_zeros(orgs)

    drop_columns = ["id"]
    orgs.drop(columns=drop_columns, inplace=True)

    is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
    if is_fares_validator_active:
        rename_map = {
            old_name: column_tuple.field_name
            for old_name, column_tuple in FEATURE_FLAG_ORG_COLUMN_MAP.items()
        }
        orgs = orgs[FEATURE_FLAG_ORG_COLUMN_MAP.keys()].rename(columns=rename_map)
    else:
        rename_map = {
            old_name: column_tuple.field_name
            for old_name, column_tuple in ORG_COLUMN_MAP.items()
        }
        orgs = orgs[ORG_COLUMN_MAP.keys()].rename(columns=rename_map)
    return orgs


def get_organisation_catalogue_csv() -> str:
    return _get_organisation_catalogue_dataframe().to_csv(index=False)
