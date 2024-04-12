import logging
from typing import List
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import factory
import pytest
from freezegun import freeze_time
from lxml import etree

from transit_odp.avl.post_publishing_checks.daily.sirivm_sampler import SirivmSampler
from transit_odp.data_quality.factories import (
    DataQualityReportFactory,
    PTIValidationResultFactory,
)
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.factories import (
    LicenceFactory,
    SeasonalServiceFactory,
    TXCFileAttributesFactory,
)
from transit_odp.otc.factories import (
    LocalAuthorityFactory,
    ServiceModelFactory,
    UILtaFactory,
)
from transit_odp.avl.factories import PostPublishingCheckReportFactory
from transit_odp.avl.models import PPCReportType
from transit_odp.avl.post_publishing_checks.models import Siri, VehicleActivity
from transit_odp.organisation.factories import DatasetFactory

logger = logging.getLogger(__name__)

DATASET_ID = 20
TEST_DATA = Path(__file__).resolve().parent / "data/siri"
DATES_REPORT = ["23/01/2023"]

pytestmark = pytest.mark.django_db


def test_get_inscope_inseason_lines():
    # setup
    start_date = f"{date.today() - timedelta(days=10)}"
    end_date = f"{date.today() + timedelta(days=10)}"
    services = ServiceModelFactory.create_batch(5, service_number="1|2|Bellford")
    for service in services:
        fa = TXCFileAttributesFactory(
            licence_number=service.licence.number,
            service_code=service.registration_number.replace("/", ":"),
        )
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)
        bods_licence = LicenceFactory(number=service.licence.number)
        SeasonalServiceFactory(
            licence=bods_licence,
            registration_code=service.registration_code,
            start=date.fromisoformat(start_date),
            end=date.fromisoformat(end_date),
        )

    ui_lta = UILtaFactory(name="Dorset County Council")
    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=services,
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)
    sirivm_sampler = SirivmSampler()
    expected_line_names = ["1", "Bellford", "2"]

    # test
    actual_line_names = sirivm_sampler.get_inscope_inseason_lines()

    # result
    for line_name in expected_line_names:
        if line_name not in actual_line_names:
            assert False


@patch.object(SirivmSampler, "get_siri_vm_data_feed_by_id")
def test_get_vehicle_activities(mock_get_siri_vm_data_feed_by_id):
    # setup
    DATA_DIR = Path(__file__).parent / "data"
    FILE_PATH = DATA_DIR / "siri_vm.xml"
    with open(FILE_PATH, "r") as f:
        xml_data = f.read()
        xml_data_bytes = bytes(xml_data, "utf-8")
    mock_get_siri_vm_data_feed_by_id.return_value = xml_data_bytes
    start_date = f"{date.today() - timedelta(days=10)}"
    end_date = f"{date.today() + timedelta(days=10)}"
    services = ServiceModelFactory.create_batch(5, service_number="100|200|Bellford")
    for service in services:
        fa = TXCFileAttributesFactory(
            licence_number=service.licence.number,
            service_code=service.registration_number.replace("/", ":"),
        )
        DataQualityReportFactory(revision=fa.revision)
        PTIValidationResultFactory(revision=fa.revision)
        bods_licence = LicenceFactory(number=service.licence.number)
        SeasonalServiceFactory(
            licence=bods_licence,
            registration_code=service.registration_code,
            start=date.fromisoformat(start_date),
            end=date.fromisoformat(end_date),
        )

    ui_lta = UILtaFactory(name="Dorset County Council")
    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=services,
    )
    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    # test
    sirivm_sampler = SirivmSampler()
    _, vehicle_activities = sirivm_sampler.get_vehicle_activities(
        feed_id=14, num_activities=1000
    )

    # result
    assert len(vehicle_activities) == 1
    assert vehicle_activities[0].monitored_vehicle_journey.line_ref == "100"


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
