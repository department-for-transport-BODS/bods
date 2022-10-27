import logging
from functools import cached_property
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import requests
from lxml import etree
from requests.exceptions import RequestException

from transit_odp.common.utils import sha1sum
from transit_odp.pipelines.constants import SCHEMA_DIR
from transit_odp.pipelines.models import SchemaDefinition

TIMEOUT = 30
logger = logging.getLogger(__name__)


class SchemaUpdater:
    """
    Class for updating zipfiles containing XML XSD schemas
    """

    def __init__(self, definition: SchemaDefinition, url: str):
        self.definition = definition
        self.url = url
        self.filename = url.split("/")[-1]

    def _fetch_content(self) -> Optional[bytes]:
        """
        Attempt to download schema zip.
        returns Response.content if successful and None otherwise
        """
        try:
            response = requests.get(self.url, timeout=TIMEOUT)

        except RequestException as exc:
            logger.warning(f"Cannot connect to server, {exc}")
            return None

        if response.ok:
            return response.content

        logger.warning(
            f"Unable to download schema zip, status code {response.status_code}"
        )

    @cached_property
    def content(self) -> Optional[bytes]:
        return self._fetch_content()

    @property
    def has_changed(self) -> bool:
        """
        compares zipfile sha1sum hash with whats in the database
        returning True if its different
        """
        if self.content is None:
            return False

        checksum = sha1sum(self.content)
        return checksum != self.definition.checksum

    def update_definition(self) -> None:
        """
        updates the content of the zipfile if its changed
        """
        if self.has_changed:
            self.definition.update_definition(self.content, self.filename)
            logger.info("Successfully updated XML schema zip")


class SchemaLoader:
    """
    Class for unzipping xsd schemas onto local filesystem
    """

    def __init__(self, definition: SchemaDefinition, xsd_path: str):
        self.definition = definition
        self._path = xsd_path
        self._schema_dir: str = SCHEMA_DIR

    @property
    def path(self) -> Path:
        """
        Returns path of main XSD file for use in schema validation.
        If the path doesnt exist in the local filesystem it is re acquired
        """
        directory = Path(self._schema_dir) / self.definition.category
        if not directory.exists():
            directory.mkdir(parents=True)
            logger.info(f"Directory {directory} created")

        path = directory / self._path

        if not path.exists():
            with ZipFile(self.definition.schema) as zin:
                for filepath in zin.namelist():
                    # Not sure why this is necessary but the netex zip triggers
                    # zip bomb warning and a couple of examples cant be extracted
                    # This is probably fine because these are known zip files from
                    # DfT
                    try:
                        zin.extract(filepath, directory)
                    except (OSError, ValueError) as e:
                        logger.warning(f"Could not extract {filepath} - {e}")
                        # We probably want to fail the pipeline if there are any other
                        # exceptions

        return path

    @property
    def schema(self) -> etree.XMLSchema:
        """
        Return a complete XSD XMLSchema object
        """
        with self.path.open("r") as f:
            doc = etree.parse(f)
            return etree.XMLSchema(doc)
