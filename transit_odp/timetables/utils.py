import logging
from pathlib import Path

from django.db.models import Q
from tenacity import retry
from tenacity.stop import stop_after_attempt

from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.models import Dataset
from transit_odp.timetables.constants import TXC_MAP
from transit_odp.timetables.pti import DatasetPTIValidator
from transit_odp.validate.xml import get_lxml_schema

logger = logging.getLogger(__name__)

PTI_PATH = Path(__file__).parent / "pti_schema.json"


class TxCSchemaDownloader:
    schema_cache = {}

    def get_transxchange_schema(self, version):
        """Gets an lxml schema object from a TxC schema_version string.

        Args:
            schema_version (str): A TxC schema version, either '2.1' or '2.4'.

        Returns:
            lxml.etree.XMLSchema: An lxml TxC schema object or None is not a
            correct version.

        """
        logger.info(f"[TransXChange] => Downloading v{version}.")
        url = TXC_MAP.get(version, None)

        if version in self.schema_cache:
            logger.warning(f"[TransXChange] => Getting {version} from cache.")
            return self.schema_cache[version]

        if url is not None:
            schema = get_lxml_schema(url)
            logger.warning(f"[TransXChange] => Download of v{version} successful.")
            self.schema_cache[version] = schema
            return schema


_txc_downloader = TxCSchemaDownloader()


@retry(stop=stop_after_attempt(5))
def get_transxchange_schema(version):
    """Wrapper around _txc_downloader singleton to provide a nicer api."""
    return _txc_downloader.get_transxchange_schema(version)


def get_remote_timetables():
    """Return a list of all the Timetable datasets that were uploaded via url."""
    is_timetable = Q(dataset_type=TimetableType)
    timetables = (
        Dataset.objects.select_related("organisation")
        .select_related("live_revision")
        .select_related("live_revision__availability_retry_count")
        .get_active()
        .get_remote()
        .filter(is_timetable)
    )
    return timetables


def get_available_remote_timetables():
    count_is_zero = Q(live_revision__availability_retry_count__count=0)
    count_is_null = Q(live_revision__availability_retry_count__isnull=True)
    timetables = get_remote_timetables().filter(count_is_zero | count_is_null)
    return timetables


def get_unavailable_remote_timetables():
    """Return a list of all the Timetable datasets that were uploaded via url and
    have a retry count greater than zero (have been unavailable)."""
    count_gt_zero = Q(live_revision__availability_retry_count__count__gt=0)
    timetables = get_remote_timetables().filter(count_gt_zero)
    return timetables


def get_pti_validator():
    """
    Gets a PTI JSON Schema and returns a DatasetPTIValidator.
    """
    with PTI_PATH.open("r") as f:
        pti = DatasetPTIValidator(f)
    return pti
