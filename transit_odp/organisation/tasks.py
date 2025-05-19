import pandas as pd
from logging import getLogger
from celery import shared_task
from waffle import flag_is_active
from transit_odp.common.constants import FeatureFlags
from transit_odp.organisation.models.organisations import Organisation
from transit_odp.organisation.models.report import ComplianceReport


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
    for operator in organisation_qs:
        organisation_calcualte_sra(operator)
    logger.info("Finished updating operator/organisation service require attention")


def organisation_calcualte_sra(
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
