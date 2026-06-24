import pytest
import json
from io import BytesIO
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError

from transit_odp.otc.weca.client import WecaClient


def test_weca_client_reads_s3_json(weca_get_agliebase_data):

    payload_bytes = json.dumps(weca_get_agliebase_data).encode("utf-8")

    # Make a mock S3 client whose get_object returns {'Body': <file-like>}
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": BytesIO(payload_bytes)}

    # Patch where boto3.client is referenced inside the module under test
    with patch("transit_odp.otc.weca.client.boto3.client", return_value=mock_s3):
        client = WecaClient()
        response = client.fetch_weca_services()

    assert len(response.fields) == 12
    assert len(response.data) == 5


def test_weca_client_fails_s3_json(weca_get_agliebase_data):

    # Make a mock S3 client whose get_object returns {'Body': <file-like>}
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": None}

    # Patch where boto3.client is referenced inside the module under test
    with patch("transit_odp.otc.weca.client.boto3.client", return_value=None):
        client = WecaClient()
        response = client.fetch_weca_services()
        assert len(response.fields) == 0
        assert len(response.data) == 0
