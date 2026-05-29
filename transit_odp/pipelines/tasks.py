from collections import namedtuple

from celery import shared_task
from celery.utils.log import get_task_logger

from transit_odp.data_quality.tasks import run_dqs_monitoring
from transit_odp.fares.netex import NETEX_SCHEMA_ZIP_URL
from transit_odp.pipelines.constants import SchemaCategory
from transit_odp.pipelines.models import SchemaDefinition
from transit_odp.pipelines.pipelines.naptan_etl import main
from transit_odp.pipelines.pipelines.xml_schema import SchemaUpdater
from transit_odp.timetables.constants import TXC_SCHEMA_ZIP_URL

logger = get_task_logger(__name__)
XMLSchemaDetails = namedtuple("XMLSchemaDetails", ["category", "url"])


@shared_task(ignore_result=True)
def task_dqs_monitor():
    """A task that monitors the Data Quality Service."""
    logger.info("[Monitoring] => Starting DQS monitoring job.")
    run_dqs_monitoring()


@shared_task(ignore_result=True)
def task_run_naptan_etl():
    main.run()


@shared_task
def task_update_xsd_zip_cache():
    details = (
        XMLSchemaDetails(SchemaCategory.TXC, TXC_SCHEMA_ZIP_URL),
        XMLSchemaDetails(SchemaCategory.NETEX, NETEX_SCHEMA_ZIP_URL),
    )
    for detail in details:
        definition, _ = SchemaDefinition.objects.get_or_create(category=detail.category)
        schema = SchemaUpdater(definition, detail.url)
        schema.update_definition()
