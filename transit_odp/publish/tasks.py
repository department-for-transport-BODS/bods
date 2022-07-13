import io
import logging
from zipfile import ZIP_DEFLATED, ZipFile

from celery import shared_task
from django.core.files.base import File
from django.utils.timezone import now

from transit_odp.organisation.csv.consumer_interactions import (
    CSV_HEADERS,
    filter_interactions_to_organisation,
    get_all_monthly_breakdown_stats,
)
from transit_odp.organisation.models import Organisation
from transit_odp.organisation.models.data import ConsumerStats
from transit_odp.publish.constants import INTERACTIONS_DEFINITION
from transit_odp.publish.stats import get_all_consumer_interaction_stats
from transit_odp.publish.views.reporting import ASSETS

logger = logging.getLogger(__name__)


@shared_task
def task_generate_monthly_consumer_interaction_breakdowns():
    records = []
    all_interactions = get_all_monthly_breakdown_stats()
    org_ids = all_interactions.organisation_id.unique()
    organisations = Organisation.objects.select_related("stats").filter(id__in=org_ids)
    logger.info("Successfully retrieved data from database")

    for organisation in organisations:
        logger.info(
            f"Generating consumer activity breakdown csv for {organisation.name}"
        )
        buffer_ = io.BytesIO()
        df = filter_interactions_to_organisation(all_interactions, organisation.id)
        csv = df.to_csv(index=False, header=CSV_HEADERS)
        common_name = f"Consumer_metrics_{organisation.name}_{now():%d%m%y}"
        zip_filename = f"{common_name}.zip"
        csv_filename = f"{common_name}.csv"
        with ZipFile(buffer_, mode="w", compression=ZIP_DEFLATED) as zin:
            zin.writestr(csv_filename, csv)
            zin.write(ASSETS / INTERACTIONS_DEFINITION, INTERACTIONS_DEFINITION)

        buffer_.seek(0)
        archive = File(buffer_, name=zip_filename)
        record = organisation.stats
        record.monthly_breakdown.delete()
        record.monthly_breakdown.save(zip_filename, archive)
        records.append(record)

    ConsumerStats.objects.bulk_update(records, fields=["monthly_breakdown"])


@shared_task
def task_generate_consumer_interaction_stats():
    records = []
    all_interactions = get_all_consumer_interaction_stats()
    org_ids = all_interactions.organisation_id.unique()

    organisations = Organisation.objects.select_related("stats").filter(id__in=org_ids)
    logger.info("Successfully retrieved data from database")

    for organisation in organisations:
        logger.info(
            f"Calculating weekly consumer activity stats for {organisation.name}"
        )
        df = filter_interactions_to_organisation(all_interactions, organisation.id)
        record = organisation.stats
        row = df.iloc[0]
        record.weekly_unique_consumers = row.unique_users
        record.weekly_downloads = row.direct_downloads_total + row.bulk_downloads_total
        record.weekly_api_hits = row.api_direct_hits_total + row.api_list_hits_total
        records.append(record)

    ConsumerStats.objects.bulk_update(
        records,
        fields=["weekly_unique_consumers", "weekly_downloads", "weekly_api_hits"],
    )
