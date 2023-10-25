import logging
import requests

from django.conf import settings
from requests import RequestException


logger = logging.getLogger(__name__)


def get_disruptions_data_catalogue_csv() -> str:
    URL = f"{settings.DISRUPTIONS_API_BASE_URL}/data-catalogue"

    try:
        response = requests.get(
            URL, headers={"x-api-key": settings.DISRUPTIONS_API_KEY}
        )

        logger.info(
            f"Request to {URL} took {response.elapsed.total_seconds()} seconds for get_disruptions_data_catalogue_csv"
        )    

        return response.text
    except RequestException:
        logger.error("Unable to retrieve disruptions data catalogue.", exc_info=True)
        raise
