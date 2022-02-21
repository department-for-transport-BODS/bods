import logging

from tenacity import retry
from tenacity.stop import stop_after_attempt

from transit_odp.timetables.constants import TXC_MAP
from transit_odp.validate.xml import get_lxml_schema

logger = logging.getLogger(__name__)


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
