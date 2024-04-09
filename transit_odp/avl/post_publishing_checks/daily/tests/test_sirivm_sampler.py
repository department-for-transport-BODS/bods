from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from unittest.mock import patch

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
from transit_odp.avl.post_publishing_checks.daily.sirivm_sampler import SirivmSampler


pytestmark = pytest.mark.django_db


def test_get_inscope_inseason_lines():
    # setup
    start_date = "2023-02-01"
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
    start_date = "2023-02-01"
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
