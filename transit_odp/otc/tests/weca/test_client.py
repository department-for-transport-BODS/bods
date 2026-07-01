import pytest
import json
from io import StringIO
from unittest.mock import patch, MagicMock

from transit_odp.otc.weca.client import WecaClient


def test_weca_client_reads_s3_json(weca_get_agliebase_data):

    # Mock S3 storage
    mock_storage = MagicMock()
    mock_storage.open.return_value.__enter__.return_value = StringIO(
        json.dumps(weca_get_agliebase_data)
    )
    # Patch where boto3.client is referenced inside the module under test
    with patch(
        "transit_odp.otc.weca.client.get_s3_bucket_storage",
        return_value=mock_storage,
    ):
        client = WecaClient()
        response = client.fetch_weca_services()

    assert len(response.fields) == 12
    assert len(response.data) == 5


def test_weca_client_fails_s3_json():

    # Make a mock S3 storage who fails on get file
    mock_storage = MagicMock()
    mock_storage.open.side_effect = FileNotFoundError("missing file")

    with patch(
        "transit_odp.otc.weca.client.get_s3_bucket_storage",
        return_value=mock_storage,
    ):
        client = WecaClient()
        response = client.fetch_weca_services()
        assert len(response.fields) == 0
        assert len(response.data) == 0
