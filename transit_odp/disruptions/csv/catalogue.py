import logging
from collections import OrderedDict

import requests
from django.conf import settings
from requests import RequestException

from transit_odp.common.collections import Column

logger = logging.getLogger(__name__)

# Needed for guidance .txt file and data catalogue guide me page
DISRUPTIONS_COLUMN_MAP = OrderedDict(
    {
        "organisation": Column(
            "Organisation",
            "The name of the organisation publishing the disruptions data.",
        ),
        "situation_number": Column(
            "Situation Number",
            "The internal BODS generated ID of the disruption.",
        ),
        "validity_start_date": Column(
            "Validity Start Date",
            "The start date of the disruption provided by the publisher to BODS.",
        ),
        "validity_end_date": Column(
            "Validity End Date",
            "The end date of the disruption provided by the publisher to BODS.",
        ),
        "publication_start_date": Column(
            "Publication Start Date",
            (
                "The start date of the publication window for the "
                "disruption provided by the publisher to BODS."
            ),
        ),
        "publication_end_date": Column(
            "Publication End Date",
            (
                "The end date of the publication window for the "
                "disruption provided by the publisher to BODS."
            ),
        ),
        "reason": Column(
            "Reason",
            "The reason for the disruption provided by the publisher to BODS.",
        ),
        "planned": Column(
            "Planned",
            (
                "The planned or unplanned nature of the disruption "
                "provided to the publisher to BODS."
            ),
        ),
        "modes_affected": Column(
            "Modes Affected",
            "The modes of public transport affected by the disruption.",
        ),
        "operators_affected": Column(
            "Operators Affected",
            "The operators of services affected by the disruption.",
        ),
        "services_affected": Column(
            "Services Affected",
            "The total number of services affected by the disruption.",
        ),
        "stops_affected": Column(
            "Stops Affected",
            "The total number of stops affected by the disruption.",
        ),
    }
)


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
