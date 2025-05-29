from logging import getLogger
from typing import List

import pandas as pd
from celery import shared_task
from waffle import flag_is_active

from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.browse.common import get_in_scope_in_season_services_line_level
from transit_odp.common.constants import FeatureFlags
from transit_odp.organisation.models.organisations import Organisation
from transit_odp.organisation.models.report import ComplianceReport
from transit_odp.publish.requires_attention import (
    FaresRequiresAttention,
    get_avl_requires_attention_line_level_data,
    get_requires_attention_line_level_data,
)

logger = getLogger(__name__)


@shared_task()
def task_precalculate_operator_sra():
    """
    Task to pre-calculate SRA for all the operators present in the database
    We will fetch ABODS lines and Vehicle activity values here because can
    be used for all the organisations. To avoid un-necessary hits
    """
    logger.info("Executing the job for operator/organisation service require attention")
    is_operator_prefetch_sra_active = flag_is_active(
        "", FeatureFlags.OPERATOR_PREFETCH_SRA.value
    )

    is_operator_prefetch_sra_from_db_active = flag_is_active(
        "", FeatureFlags.OPERATOR_PREFETCH_SRA_FROM_DB.value
    )

    if not is_operator_prefetch_sra_active:
        logger.info(
            f"Flag {FeatureFlags.OPERATOR_PREFETCH_SRA.value} is not active, skipping the execution."
        )
        return

    if is_operator_prefetch_sra_from_db_active:
        logger.info("Precalcuate operator sra from database.")
        precalculate_from_db()
    else:
        logger.info("Precalcuate operator sra from compliance report.")
        precalculate_from_compliance_report()

    logger.info("Finished updating operator/organisation service require attention")


def organisation_calcualte_sra_from_compliance_report(
    organisation: Organisation,
):
    """SRA calculation for single operator/organisation

    Args:
        organisation (Organisation): Organisation object
        uncounted_activity_df (pd.DataFrame): vehicle activity value
        synced_in_last_month (List): Abods lines list
    """
    try:
        organisation_compliance_df = pd.DataFrame.from_records(
            ComplianceReport.objects.filter(
                licence_organisation_id=organisation.id, scope_status="In Scope"
            )
            .exclude(seasonal_status="Out of Season")
            .values(
                "registration_number",
                "service_number",
                "otc_licence_number",
                "requires_attention",
                "overall_requires_attention",
                "fares_requires_attention",
                "avl_requires_attention",
                "scope_status",
            )
        )

        overall_sra = total_inscope = avl_sra = fares_sra = timetable_sra = 0
        if not organisation_compliance_df.empty:
            total_inscope = len(organisation_compliance_df)
            timetable_sra = len(
                organisation_compliance_df[
                    organisation_compliance_df["requires_attention"] == "Yes"
                ]
            )
            avl_sra = len(
                organisation_compliance_df[
                    organisation_compliance_df["avl_requires_attention"] == "Yes"
                ]
            )
            fares_sra = len(
                organisation_compliance_df[
                    organisation_compliance_df["fares_requires_attention"] == "Yes"
                ]
            )
            overall_sra = len(
                organisation_compliance_df[
                    organisation_compliance_df["overall_requires_attention"] == "Yes"
                ]
            )

        organisation.overall_sra = overall_sra
        organisation.total_inscope = total_inscope
        organisation.avl_sra = avl_sra
        organisation.fares_sra = fares_sra
        organisation.timetable_sra = timetable_sra
        organisation.save()
    except Exception as e:
        logger.error(f"Error occured while syncing sra for {organisation.name}")
        logger.exception(e)


def precalculate_from_compliance_report():
    """
    Method will use compliance report table to calculate the SRA value for all the operators
    """
    logger.info(
        "Executing the job for operator/organisation service require attention from compliance report"
    )
    organisation_qs = Organisation.objects.all()
    logger.info(f"Total operators found {organisation_qs.count()}")
    for operator in organisation_qs:
        organisation_calcualte_sra_from_compliance_report(operator)


def precalculate_from_db():
    """
    Task to pre-calculate SRA for all the operators present in the database
    We will fetch ABODS lines and Vehicle activity values here because can
    be used for all the organisations. To avoid un-necessary hits
    """
    logger.info(
        "Executing the job for operator/organisation service require attention from database"
    )
    is_avl_require_attention_active = flag_is_active(
        "", FeatureFlags.AVL_REQUIRES_ATTENTION.value
    )
    organisation_qs = Organisation.objects.all()
    logger.info(f"Total operators found {organisation_qs.count()}")

    if is_avl_require_attention_active:
        uncounted_activity_df = get_vehicle_activity_operatorref_linename()
        abods_registry = AbodsRegistery()
        synced_in_last_month = abods_registry.records()
    else:
        uncounted_activity_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
        synced_in_last_month = []

    logger.info(
        f"Step: Starting orgnaisation level processing. With Synced in last month {len(synced_in_last_month)} Uncounded vehicle activity df {uncounted_activity_df.shape}"
    )
    for operator in organisation_qs:
        organisation_calcualte_sra_from_db(
            operator, uncounted_activity_df, synced_in_last_month
        )
    logger.info("Finished updating operator/organisation service require attention")


def organisation_calcualte_sra_from_db(
    organisation: Organisation,
    uncounted_activity_df: pd.DataFrame,
    synced_in_last_month: List,
):
    """SRA calculation for single operator/organisation

    Args:
        organisation (Organisation): Organisation object
        uncounted_activity_df (pd.DataFrame): vehicle activity value
        synced_in_last_month (List): Abods lines list
    """
    try:
        timetable_sra = get_requires_attention_line_level_data(organisation.id)
        in_scope_services = get_in_scope_in_season_services_line_level(organisation.id)

        avl_sra = fares_sra = []

        is_avl_require_attention_active = flag_is_active(
            "", FeatureFlags.AVL_REQUIRES_ATTENTION.value
        )
        is_fares_require_attention_active = flag_is_active(
            "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
        )

        if is_avl_require_attention_active:
            avl_sra = get_avl_requires_attention_line_level_data(
                organisation.id, uncounted_activity_df, synced_in_last_month
            )

        if is_fares_require_attention_active:
            fra = FaresRequiresAttention(organisation.id)
            fares_sra = fra.get_fares_requires_attention_line_level_data()

        all_sra = timetable_sra + avl_sra + fares_sra
        overall_sra = set()
        for d in all_sra:
            key = (
                d.get("licence_number")
                + "__"
                + d.get("service_code")
                + "__"
                + d.get("line_number")
            )
            overall_sra.add(key)

        organisation.total_inscope = len(in_scope_services)
        organisation.timetable_sra = len(timetable_sra)
        organisation.avl_sra = len(avl_sra)
        organisation.fares_sra = len(fares_sra)
        organisation.overall_sra = len(overall_sra)
        organisation.save()
    except Exception as e:
        logger.error(f"Error occured while syncing sra for {organisation.name}")
        logger.exception(e)
