import pandas as pd
from typing import List
from logging import getLogger
from celery import shared_task
from waffle import flag_is_active
from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.browse.common import get_in_scope_in_season_services_line_level
from transit_odp.common.constants import FeatureFlags
from transit_odp.organisation.models.organisations import Organisation
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

    if not is_operator_prefetch_sra_active:
        logger.info(
            f"Flag {FeatureFlags.OPERATOR_PREFETCH_SRA.value} is not active, skipping the execution."
        )
        return
    organisation_qs = Organisation.objects.all()
    logger.info(f"Total operators found {organisation_qs.count()}")
    uncounted_activity_df = get_vehicle_activity_operatorref_linename()
    abods_registry = AbodsRegistery()
    synced_in_last_month = abods_registry.records()
    logger.info(
        f"Step: Starting orgnaisation level processing. With Synced in last month {len(synced_in_last_month)} Uncounded vehicle activity df {uncounted_activity_df.shape}"
    )
    for operator in organisation_qs:
        organisation_calcualte_sra(
            operator, uncounted_activity_df, synced_in_last_month
        )
    logger.info("Finished updating operator/organisation service require attention")


def organisation_calcualte_sra(
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
        avl_sra = get_avl_requires_attention_line_level_data(
            organisation.id, uncounted_activity_df, synced_in_last_month
        )

        fra = FaresRequiresAttention(organisation.id)
        fares_sra = fra.get_fares_requires_attention_line_level_data()
        in_scope_services = get_in_scope_in_season_services_line_level(organisation.id)

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
