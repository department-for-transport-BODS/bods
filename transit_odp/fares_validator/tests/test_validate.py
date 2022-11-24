import pytest
from pathlib import Path
from django.http import JsonResponse
from rest_framework import status
from django.core.files import File
from django.conf import settings
from django_hosts.resolvers import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.fares_validator.views.validate import FaresXmlValidator
from transit_odp.fares_validator.models import FaresValidation

DATA_DIR = Path(__file__).parent / "data"

# pytestmark = pytest.mark.django_db

# @pytest.mark.parametrize(
#     (
#         "test_pass",
#         "expected",
#     ),
#     [
#         (True, 200),
#         (False, 201),
#     ],
# )
def test_set_errors(test_pass=True, expected=200):

    if test_pass:
        filepath = DATA_DIR / "fares_test_xml_pass.xml"
    else:
        filepath = DATA_DIR / "fares_test_xml_fail.xml"
    
    with open(filepath, "rb") as zout:
        fares_xml_validator = FaresXmlValidator(File(zout, name="fares_test_xml.xml"), 1, 1)
        result = fares_xml_validator.set_errors()
        if result:
            assert result.status_code == expected

# @pytest.mark.parametrize(
#     (
#         "test_pass",
#         "expected",
#     ),
#     [
#         (True, 200),
#         (False, 201),
#     ],
# )
def test_fares_validation_zip(test_pass=True, expected=200):
    if test_pass:
        filepath = DATA_DIR / "fares_test_zip_pass.zip"
    else:
        filepath = DATA_DIR / "fares_test_zip_fail.zip"
    with open(filepath, "rb") as zout:
        fares_xml_validator = FaresXmlValidator(File(zout, name="fares_test_xml.xml"), 1, 1)
        result = fares_xml_validator.set_errors()
        if result:
            assert result.status_code == expected
  