from pathlib import Path

import pytest
import requests_mock
from requests.exceptions import ConnectionError

from transit_odp.pipelines.factories import SchemaDefinitionFactory
from transit_odp.pipelines.pipelines.xml_schema import SchemaLoader, SchemaUpdater
from transit_odp.timetables.constants import TXC_XSD_PATH

pytestmark = pytest.mark.django_db
HERE = Path(__file__)
DATA = HERE.parent / "data"


@requests_mock.Mocker(kw="m")
def test_matching_checksums_dont_update(**kwargs):
    schema = SchemaDefinitionFactory()
    old_checksum = schema.checksum
    url = "http://test.example.com/path/to/schema_definition.zip"
    kwargs["m"].get(
        url,
        content=schema.schema.read(),
        headers={"Content-Type": "application/x-zip-compressed"},
    )
    updater = SchemaUpdater(schema, url)
    updater.update_definition()
    schema.refresh_from_db()
    assert old_checksum == schema.checksum


@requests_mock.Mocker(kw="m")
def test_mismatching_checksums_update(**kwargs):
    schema = SchemaDefinitionFactory()
    old_checksum = schema.checksum
    url = "http://test.example.com/path/to/schema_definition.zip"
    kwargs["m"].get(
        url,
        content=b"new data",
        headers={"Content-Type": "application/x-zip-compressed"},
    )
    updater = SchemaUpdater(schema, url)
    updater.update_definition()
    schema.refresh_from_db()
    assert old_checksum != schema.checksum


@requests_mock.Mocker(kw="m")
def test_simulated_connection_error(**kwargs):
    schema = SchemaDefinitionFactory()
    old_checksum = schema.checksum
    url = "http://test.example.com/path/to/schema_definition.zip"
    kwargs["m"].get(url, exc=ConnectionError)
    updater = SchemaUpdater(schema, url)
    updater.update_definition()
    schema.refresh_from_db()
    assert old_checksum == schema.checksum


@requests_mock.Mocker(kw="m")
def test_simulated_not_found(**kwargs):
    schema = SchemaDefinitionFactory()
    old_checksum = schema.checksum
    url = "http://test.example.com/path/to/schema_definition.zip"
    kwargs["m"].get(url, status_code=404)
    updater = SchemaUpdater(schema, url)
    updater.update_definition()
    schema.refresh_from_db()
    assert old_checksum == schema.checksum


def test_schema_loader_can_unzip(tmp_path):
    schema = SchemaDefinitionFactory(
        schema__from_path=DATA / "TransXChange_schema_2.4.zip"
    )
    loader = SchemaLoader(schema, TXC_XSD_PATH)
    loader._schema_dir = tmp_path
    assert loader.path == tmp_path / "TxC" / Path(TXC_XSD_PATH)
    assert loader.path.exists()
