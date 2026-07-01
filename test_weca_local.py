import os
import json
import dotenv
import logging

dotenv.load_dotenv(".env.weca_local")

import django
from django.conf import settings

# Configure Django for Lambda environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

# Django bootstrap - required for Lambda to load models and utilities
if not settings.configured:
    django.setup()

from transit_odp.pipelines.pipelines.weca_extract_etl.extract import get_latest_data

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

if __name__ == "__main__":

    test_services = {
        "url": "https://registrations.travelwest.info/agileBase/Public.ab",
        "api_key": "rwt4kzodylvyxad08d9jxdbdsp4djr94wq",
        "param_c": "pt7atfu9e78z39yqc",
        "param_t": "services_pt7atfu9e78z39yqc",
        "param_r": "copyofservicesl_vicespt7at01237",
    }
    test_registrations = {
        "url": "https://registrations.travelwest.info/agileBase/Public.ab",
        "api_key": "vmao8drpfndudpgdcrqcap8hp7mbhwzokf",
        "param_c": "pt7atfu9e78z39yqc",
        "param_t": "services_pt7atfu9e78z39yqc",
        "param_r": "copyof2register_vicespt7at0",
    }

    logger.info("Starting WECA Test")
    metadata = get_latest_data(test_services, test_registrations)

    logger.info(f"Results: {json.dumps(metadata, indent=4)}")
