import logging
from datetime import datetime
from pathlib import Path
from typing import List

import factory
import pytest
from freezegun import freeze_time
from lxml import etree

from transit_odp.avl.factories import PostPublishingCheckReportFactory
from transit_odp.avl.models import PPCReportType
from transit_odp.avl.post_publishing_checks.daily.sirivm_sampler import SirivmSampler
from transit_odp.avl.post_publishing_checks.models import Siri, VehicleActivity
from transit_odp.organisation.factories import DatasetFactory

logger = logging.getLogger(__name__)
pytestmark = pytest.mark.django_db

DATASET_ID = 20
TEST_DATA = Path(__file__).resolve().parent / "data/siri"
DATES_REPORT = ["23/01/2023"]


def get_vehicle_activities(file_name="siri_sample.xml") -> List[VehicleActivity]:
    """Read Sample SIRI file and get the vehicle activities

    Returns:
        List[VehicleActivity]: List of vehicle activities
    """
    xml_file_path = f"{TEST_DATA}/{file_name}"
    try:
        with open(xml_file_path, "r") as file:
            xml_content = file.read()
    except IOError:
        logger.error("Error: File not found or could not be read.")
    except etree.XMLSyntaxError:
        logger.error("Error: Invalid XML syntax in the file.")

    siri = Siri.from_string(xml_content)
    return (
        siri.service_delivery.vehicle_monitoring_delivery.vehicle_activities,
        siri.service_delivery.vehicle_monitoring_delivery.response_timestamp.date(),
    )


def load_post_publishing_checks_reports_data():
    for report_date in DATES_REPORT:
        date_str = report_date.replace("/", "_")
        filename = f"day_{date_str}_feed.json"
        report_file = TEST_DATA / filename
        PostPublishingCheckReportFactory(
            dataset=DatasetFactory(id=DATASET_ID),
            granularity=PPCReportType.DAILY,
            created=datetime.strptime(report_date, "%d/%m/%Y").date(),
            file=factory.django.FileField(from_path=report_file, filename=filename),
            vehicle_activities_analysed=2,
            vehicle_activities_completely_matching=2,
        )


@freeze_time("2023-01-25")
def test_ignore_old_activites_include_all():
    siri_sampler = SirivmSampler()
    vehicle_activities_siri_response, response_date = get_vehicle_activities()
    vehicle_activities = siri_sampler.ignore_old_activites(
        vehicle_activities_siri_response, response_date, DATASET_ID
    )
    assert len(vehicle_activities) == 2


@freeze_time("2023-01-25")
def test_vehicle_activites_ignore_second_timer():
    siri_sampler = SirivmSampler()
    load_post_publishing_checks_reports_data()
    vehicle_activities_siri_response, response_date = get_vehicle_activities()
    vehicle_activities = siri_sampler.ignore_old_activites(
        vehicle_activities_siri_response, response_date, DATASET_ID
    )

    assert len(vehicle_activities) == 0


@freeze_time("2023-01-25")
def test_vehicle_activites_ignore_old_first_timer():
    siri_sampler = SirivmSampler()
    vehicle_activities_siri_response, response_date = get_vehicle_activities(
        "siri_sample_with_old_va.xml"
    )
    vehicle_activities = siri_sampler.ignore_old_activites(
        vehicle_activities_siri_response, response_date, DATASET_ID
    )

    assert len(vehicle_activities) == 1
