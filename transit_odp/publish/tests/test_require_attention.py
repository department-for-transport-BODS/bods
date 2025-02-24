# from django.utils.timezone import now
# from datetime import timedelta
from freezegun import freeze_time
import pandas as pd
from unittest.mock import MagicMock, patch
import datetime
import pytest
from transit_odp.dqs.constants import Level, TaskResultsStatus
from waffle.testutils import override_flag
from transit_odp.organisation.factories import (
    ConsumerFeedbackFactory,
    TXCFileAttributesFactory,
)
from django.utils import timezone
import transit_odp.publish.requires_attention as publish_attention
from transit_odp.publish.requires_attention import (
    get_avl_records_require_attention_lta_line_level_length,
    get_timetable_records_require_attention_lta_line_level_length,
)

from transit_odp.dqs.factories import (
    ChecksFactory,
    TaskResultsFactory,
    ObservationResultsFactory,
)
from transit_odp.organisation.models.data import TXCFileAttributes
from transit_odp.publish.requires_attention import (
    get_dq_critical_observation_services_map,
)
from transit_odp.transmodel.factories import (
    ServiceFactory,
    ServicePatternFactory,
    ServicePatternStopFactory,
)
from transit_odp.otc.factories import (
    LicenceModelFactory,
    LocalAuthorityFactory,
    ServiceModelFactory,
    UILtaFactory,
)
from transit_odp.organisation.factories import (
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.factories import (
    DatasetFactory,
    DraftDatasetFactory,
)
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.otc.models import LocalAuthority
from transit_odp.otc.models import Service as OTCService


pytestmark = pytest.mark.django_db


@override_flag("dqs_require_attention", active=True)
@override_flag("is_specific_feedback", active=False)
def test_dq_require_attention_with_only_critical_observation_results():
    services_list = [
        {
            "licence": f"PD000000{i}",
            "service_code": f"PD000000{i}:{i}",
            "line_name": [f"L{i}"],
        }
        for i in range(0, 11)
    ]

    txcfileattributes = []
    for service in services_list:
        txcfileattributes.append(
            TXCFileAttributesFactory(
                service_code=service["service_code"], line_names=service["line_name"]
            )
        )

    check1 = ChecksFactory(importance=Level.critical.value)
    check2 = ChecksFactory(importance=Level.advisory.value)

    services_with_critical = []
    services_with_advisory = []
    for i, txcfileattribute in enumerate(txcfileattributes):
        check_obj = check1 if i % 2 == 0 else check2
        if check_obj.importance == Level.critical.value:
            services_with_critical.append(
                (txcfileattribute.service_code, txcfileattribute.line_names[0])
            )
        else:
            services_with_advisory.append(
                (txcfileattribute.service_code, txcfileattribute.line_names[0])
            )

        task_result = TaskResultsFactory(
            status=TaskResultsStatus.PENDING.value,
            transmodel_txcfileattributes=txcfileattribute,
            checks=check_obj,
        )
        service_pattern = ServicePatternFactory(
            revision=txcfileattribute.revision, line_name=txcfileattribute.line_names[0]
        )
        ServiceFactory(
            revision=txcfileattribute.revision,
            service_code=txcfileattribute.service_code,
            name=txcfileattribute.line_names[0],
            service_patterns=[service_pattern],
            txcfileattributes=txcfileattribute,
        )

        service_pattern_stop = ServicePatternStopFactory(
            service_pattern=service_pattern
        )

        ObservationResultsFactory(
            service_pattern_stop=service_pattern_stop, taskresults=task_result
        )

    txc_files = {
        obj.id: obj for obj in TXCFileAttributes.objects.add_split_linenames().all()
    }
    dq_services = get_dq_critical_observation_services_map(txc_files)

    assert sorted(services_with_critical, key=lambda tup: tup[0]) == sorted(
        dq_services, key=lambda tup: tup[0]
    )

    assert len(services_with_critical) == len(dq_services)


@override_flag("dqs_require_attention", active=True)
@override_flag("is_specific_feedback", active=True)
def test_dq_require_attention_with_only_critical_observation_results_with_feedback_flag():
    services_list = [
        {
            "licence": f"PD000000{i}",
            "service_code": f"PD000000{i}:{i}",
            "line_name": [f"L{i}"],
        }
        for i in range(0, 11)
    ]

    txcfileattributes = []
    for service in services_list:
        txcfileattributes.append(
            TXCFileAttributesFactory(
                service_code=service["service_code"], line_names=service["line_name"]
            )
        )

    check1 = ChecksFactory(importance=Level.critical.value)
    check2 = ChecksFactory(importance=Level.advisory.value)

    services_with_critical = []
    services_with_advisory = []
    for i, txcfileattribute in enumerate(txcfileattributes):
        check_obj = check1 if i % 2 == 0 else check2
        if check_obj.importance == Level.critical.value:
            services_with_critical.append(
                (txcfileattribute.service_code, txcfileattribute.line_names[0])
            )
        else:
            services_with_advisory.append(
                (txcfileattribute.service_code, txcfileattribute.line_names[0])
            )

        task_result = TaskResultsFactory(
            status=TaskResultsStatus.PENDING.value,
            transmodel_txcfileattributes=txcfileattribute,
            checks=check_obj,
        )
        service_pattern = ServicePatternFactory(
            revision=txcfileattribute.revision, line_name=txcfileattribute.line_names[0]
        )
        ServiceFactory(
            revision=txcfileattribute.revision,
            service_code=txcfileattribute.service_code,
            name=txcfileattribute.line_names[0],
            service_patterns=[service_pattern],
            txcfileattributes=txcfileattribute,
        )

        service_pattern_stop = ServicePatternStopFactory(
            service_pattern=service_pattern
        )

        ObservationResultsFactory(
            service_pattern_stop=service_pattern_stop, taskresults=task_result
        )

    txc_files = {
        obj.id: obj for obj in TXCFileAttributes.objects.add_split_linenames().all()
    }
    dq_services = get_dq_critical_observation_services_map(txc_files)

    assert sorted(services_with_critical, key=lambda tup: tup[0]) == sorted(
        dq_services, key=lambda tup: tup[0]
    )

    assert len(services_with_critical) == len(dq_services)


@override_flag("dqs_require_attention", active=True)
@override_flag("is_specific_feedback", active=True)
def test_dq_require_attention_with_only_advisory_observation_results():
    services_list = [
        {
            "licence": f"PD000000{i}",
            "service_code": f"PD000000{i}:{i}",
            "line_name": [f"L{i}"],
        }
        for i in range(0, 11)
    ]

    txcfileattributes = []
    for service in services_list:
        txcfileattributes.append(
            TXCFileAttributesFactory(
                service_code=service["service_code"], line_names=service["line_name"]
            )
        )

    check1 = ChecksFactory(importance=Level.critical.value)
    check2 = ChecksFactory(importance=Level.advisory.value)

    services_with_critical = []
    services_with_advisory = []
    for i, txcfileattribute in enumerate(txcfileattributes):
        check_obj = check1 if i % 2 == 0 else check2
        if check_obj.importance == Level.critical.value:
            services_with_critical.append(
                (txcfileattribute.service_code, txcfileattribute.line_names[0])
            )
        else:
            services_with_advisory.append(
                (txcfileattribute.service_code, txcfileattribute.line_names[0])
            )

        task_result = TaskResultsFactory(
            status=TaskResultsStatus.PENDING.value,
            transmodel_txcfileattributes=txcfileattribute,
            checks=check_obj,
        )
        service_pattern = ServicePatternFactory(
            revision=txcfileattribute.revision, line_name=txcfileattribute.line_names[0]
        )
        ServiceFactory(
            revision=txcfileattribute.revision,
            service_code=txcfileattribute.service_code,
            name=txcfileattribute.line_names[0],
            service_patterns=[service_pattern],
        )

        service_pattern_stop = ServicePatternStopFactory(
            service_pattern=service_pattern
        )
        if check_obj.importance == Level.advisory.value:
            ObservationResultsFactory(
                service_pattern_stop=service_pattern_stop, taskresults=task_result
            )

    txc_files = {
        obj.id: obj for obj in TXCFileAttributes.objects.add_split_linenames().all()
    }
    dq_services = get_dq_critical_observation_services_map(txc_files)

    assert 0 == len(dq_services)


@override_flag("dqs_require_attention", active=True)
@override_flag("is_specific_feedback", active=True)
def test_dq_require_attention_with_only_feedback():
    services_list = [
        {
            "licence": f"PD000000{i}",
            "service_code": f"PD000000{i}:{i}",
            "line_name": [f"L{i}"],
        }
        for i in range(0, 11)
    ]
    services_objects = []
    for service in services_list:
        txcfileattribute = TXCFileAttributesFactory(
            service_code=service["service_code"], line_names=service["line_name"]
        )

        service_pattern = ServicePatternFactory(
            revision=txcfileattribute.revision, line_name=txcfileattribute.line_names[0]
        )

        services_objects.append(
            ServiceFactory(
                revision=txcfileattribute.revision,
                service_code=txcfileattribute.service_code,
                name=txcfileattribute.line_names[0],
                service_patterns=[service_pattern],
                txcfileattributes=txcfileattribute,
            )
        )

    ConsumerFeedbackFactory(service=services_objects[0], is_suppressed=False)
    ConsumerFeedbackFactory(service=services_objects[1], is_suppressed=True)

    txc_files = {
        obj.id: obj for obj in TXCFileAttributes.objects.add_split_linenames().all()
    }
    dq_services = get_dq_critical_observation_services_map(txc_files)

    assert 1 == len(dq_services)
    assert services_objects[0].service_code == dq_services[0][0]


@override_flag("dqs_require_attention", active=True)
@override_flag("is_specific_feedback", active=True)
def test_dq_require_attention_without_feedback_and_dqsobservation():
    services_list = [
        {
            "licence": f"PD000000{i}",
            "service_code": f"PD000000{i}:{i}",
            "line_name": [f"L{i}"],
        }
        for i in range(0, 11)
    ]
    services_objects = []
    for service in services_list:
        txcfileattribute = TXCFileAttributesFactory(
            service_code=service["service_code"], line_names=service["line_name"]
        )

        service_pattern = ServicePatternFactory(
            revision=txcfileattribute.revision, line_name=txcfileattribute.line_names[0]
        )

        services_objects.append(
            ServiceFactory(
                revision=txcfileattribute.revision,
                service_code=txcfileattribute.service_code,
                name=txcfileattribute.line_names[0],
                service_patterns=[service_pattern],
            )
        )

    txc_files = {
        obj.id: obj for obj in TXCFileAttributes.objects.add_split_linenames().all()
    }
    dq_services = get_dq_critical_observation_services_map(txc_files)

    assert 0 == len(dq_services)


@override_flag("dqs_require_attention", active=True)
@override_flag("is_specific_feedback", active=True)
def test_dq_require_attention_with_feedback_and_dqsobservation():
    services_list = [
        {
            "licence": f"PD000000{i}",
            "service_code": f"PD000000{i}:{i}",
            "line_name": [f"L{i}"],
        }
        for i in range(0, 11)
    ]

    txcfileattributes = []
    for service in services_list:
        txcfileattributes.append(
            TXCFileAttributesFactory(
                service_code=service["service_code"], line_names=service["line_name"]
            )
        )

    check1 = ChecksFactory(importance=Level.critical.value)
    check2 = ChecksFactory(importance=Level.advisory.value)

    services_with_critical = []
    services_with_advisory = []

    for i, txcfileattribute in enumerate(txcfileattributes):
        check_obj = check1 if i % 2 == 0 else check2

        task_result = TaskResultsFactory(
            status=TaskResultsStatus.PENDING.value,
            transmodel_txcfileattributes=txcfileattribute,
            checks=check_obj,
        )
        service_pattern = ServicePatternFactory(
            revision=txcfileattribute.revision, line_name=txcfileattribute.line_names[0]
        )
        service_object = ServiceFactory(
            revision=txcfileattribute.revision,
            service_code=txcfileattribute.service_code,
            name=txcfileattribute.line_names[0],
            service_patterns=[service_pattern],
            txcfileattributes=txcfileattribute,
        )

        if check_obj.importance == Level.critical.value:
            services_with_critical.append(service_object)
        else:
            services_with_advisory.append(service_object)

        service_pattern_stop = ServicePatternStopFactory(
            service_pattern=service_pattern
        )

        ObservationResultsFactory(
            service_pattern_stop=service_pattern_stop, taskresults=task_result
        )

    ConsumerFeedbackFactory(service=services_with_critical[0], is_suppressed=False)
    ConsumerFeedbackFactory(service=services_with_critical[1], is_suppressed=True)
    ConsumerFeedbackFactory(service=services_with_advisory[0], is_suppressed=False)
    ConsumerFeedbackFactory(service=services_with_advisory[1], is_suppressed=True)

    txc_files = {
        obj.id: obj for obj in TXCFileAttributes.objects.add_split_linenames().all()
    }
    dq_services = get_dq_critical_observation_services_map(txc_files)

    services_with_dq_require_attention = services_with_critical + [
        services_with_advisory[0]
    ]

    assert sorted(
        [
            (service_obj.service_code, service_obj.name)
            for service_obj in services_with_dq_require_attention
        ],
        key=lambda tup: tup[0],
    ) == sorted(dq_services, key=lambda tup: tup[0])

    assert len(services_with_dq_require_attention) == len(dq_services)


@override_flag("dqs_require_attention", active=True)
@override_flag("is_specific_feedback", active=True)
def test_dq_require_attention_without_services():
    services_list = [
        {
            "licence": f"PD000000{i}",
            "service_code": f"PD000000{i}:{i}",
            "line_name": [f"L{i}"],
        }
        for i in range(0, 11)
    ]

    txcfileattributes = []
    for service in services_list:
        txcfileattributes.append(
            TXCFileAttributesFactory(
                service_code=service["service_code"], line_names=service["line_name"]
            )
        )

    txc_files = {
        obj.id: obj for obj in TXCFileAttributes.objects.add_split_linenames().all()
    }
    dq_services = get_dq_critical_observation_services_map(txc_files)

    assert 0 == len(dq_services)


@override_flag("dqs_require_attention", active=True)
@patch.object(publish_attention, "AbodsRegistery")
@patch.object(publish_attention, "get_vehicle_activity_operatorref_linename")
@freeze_time("2024-11-24T16:40:40.000Z")
def test_get_avl_records_require_attention_lta_line_level_length(
    mock_vehivle_activity, mock_abodsregistry
):
    mock_registry_instance = MagicMock()
    mock_abodsregistry.return_value = mock_registry_instance
    mock_registry_instance.records.return_value = ["line1__SDCU", "line2__SDCU"]
    mock_vehivle_activity.return_value = pd.DataFrame(
        {"OperatorRef": ["SDCU"], "LineRef": ["line2"]}
    )
    org = OrganisationFactory()
    total_services = 9
    licence_number = "PD5000229"
    service = []
    service_code_prefix = "1101000"
    atco_code = "110"
    all_service_codes = [
        f"{licence_number}:{service_code_prefix}{n}" for n in range(total_services)
    ]
    bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
    dataset1 = DatasetFactory(organisation=org)

    otc_lic = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        service.append(
            ServiceModelFactory(
                licence=otc_lic,
                registration_number=code.replace(":", "/"),
                effective_date=datetime.date(year=2020, month=1, day=1),
                atco_code=atco_code,
                service_number="line1",
            )
        )

    ui_lta = UILtaFactory(name="Dorset County Council")

    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=service[0:6],
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code=atco_code)

    # Setup two TXCFileAttributes that will be 'Not Stale'
    TXCFileAttributesFactory(
        revision_id=dataset1.live_revision.id,
        licence_number=otc_lic.number,
        service_code=all_service_codes[0],
        operating_period_end_date=datetime.date.today() + datetime.timedelta(days=50),
        modification_datetime=timezone.now(),
        national_operator_code="SDCU",
    )

    TXCFileAttributesFactory(
        revision_id=dataset1.live_revision.id,
        licence_number=otc_lic.number,
        service_code=all_service_codes[1],
        operating_period_end_date=datetime.date.today() + datetime.timedelta(days=75),
        modification_datetime=timezone.now() - datetime.timedelta(days=50),
        national_operator_code="SDCU",
    )

    # Setup a draft TXCFileAttributes
    dataset2 = DraftDatasetFactory(organisation=org)
    TXCFileAttributesFactory(
        revision_id=dataset2.revisions.last().id,
        licence_number=otc_lic.number,
        service_code=all_service_codes[2],
    )

    live_revision = dataset2.revisions.last()
    # Setup a TXCFileAttributes that will be 'Stale - 12 months old'
    TXCFileAttributesFactory(
        revision_id=live_revision.id,
        licence_number=otc_lic.number,
        service_code=all_service_codes[3],
        operating_period_end_date=None,
        modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
        national_operator_code="SDCU",
    )

    # Setup a TXCFileAttributes that will be 'Stale - 42 day look ahead'
    TXCFileAttributesFactory(
        revision_id=live_revision.id,
        licence_number=otc_lic.number,
        service_code=all_service_codes[4],
        operating_period_end_date=datetime.date.today() - datetime.timedelta(weeks=105),
        modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
    )

    # Setup a TXCFileAttributes that will be 'Stale - OTC Variation'
    TXCFileAttributesFactory(
        revision_id=live_revision.id,
        licence_number=otc_lic.number,
        service_code=all_service_codes[5],
        operating_period_end_date=datetime.date.today() + datetime.timedelta(days=50),
    )

    lta_objs = LocalAuthority.objects.all()
    otc_service = OTCService.objects.all()

    result = get_avl_records_require_attention_lta_line_level_length(lta_objs)
    assert result == 7
    assert len(otc_service) == 7


@override_flag("dqs_require_attention", active=True)
@freeze_time("2024-11-24T16:40:40.000Z")
def test_get_timetable_records_require_attention_lta_line_level_length():
    org = OrganisationFactory()
    total_services = 9
    licence_number = "PD5000229"
    service = []
    service_code_prefix = "1101000"
    atco_code = "110"
    all_service_codes = [
        f"{licence_number}:{service_code_prefix}{n}" for n in range(total_services)
    ]
    bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
    dataset1 = DatasetFactory(organisation=org)

    otc_lic = LicenceModelFactory(number=licence_number)
    txcfileattributes = []

    for code in all_service_codes:
        service.append(
            ServiceModelFactory(
                licence=otc_lic,
                registration_number=code.replace(":", "/"),
                effective_date=datetime.date(year=2020, month=1, day=1),
                atco_code=atco_code,
                service_number="line1",
            )
        )

    ui_lta = UILtaFactory(name="Dorset County Council")

    LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=service[0:6],
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code=atco_code)

    # Setup two TXCFileAttributes that will be 'Not Stale'
    txcfileattributes.append(
        TXCFileAttributesFactory(
            revision_id=dataset1.live_revision.id,
            licence_number=otc_lic.number,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            national_operator_code="SDCU",
        )
    )

    txcfileattributes.append(
        TXCFileAttributesFactory(
            revision_id=dataset1.live_revision.id,
            licence_number=otc_lic.number,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=75),
            modification_datetime=timezone.now() - datetime.timedelta(days=50),
            national_operator_code="SDCU",
        )
    )

    # Setup a draft TXCFileAttributes
    dataset2 = DraftDatasetFactory(organisation=org)
    txcfileattributes.append(
        TXCFileAttributesFactory(
            revision_id=dataset2.revisions.last().id,
            licence_number=otc_lic.number,
            service_code=all_service_codes[2],
        )
    )

    live_revision = dataset2.revisions.last()
    # Setup a TXCFileAttributes that will be 'Stale - 12 months old'
    txcfileattributes.append(
        TXCFileAttributesFactory(
            revision_id=live_revision.id,
            licence_number=otc_lic.number,
            service_code=all_service_codes[3],
            operating_period_end_date=None,
            modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
            national_operator_code="SDCU",
        )
    )

    # Setup a TXCFileAttributes that will be 'Stale - 42 day look ahead'
    txcfileattributes.append(
        TXCFileAttributesFactory(
            revision_id=live_revision.id,
            licence_number=otc_lic.number,
            service_code=all_service_codes[4],
            operating_period_end_date=datetime.date.today()
            - datetime.timedelta(weeks=105),
            modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
        )
    )

    # Setup a TXCFileAttributes that will be 'Stale - OTC Variation'
    txcfileattributes.append(
        TXCFileAttributesFactory(
            revision_id=live_revision.id,
            licence_number=otc_lic.number,
            service_code=all_service_codes[5],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
        )
    )

    check1 = ChecksFactory(importance=Level.critical.value)
    check2 = ChecksFactory(importance=Level.advisory.value)

    services_with_critical = []
    services_with_advisory = []
    for i, txcfileattribute in enumerate(txcfileattributes):
        check_obj = check1 if i % 2 == 0 else check2
        if check_obj.importance == Level.critical.value:
            services_with_critical.append(
                (txcfileattribute.service_code, txcfileattribute.line_names[0])
            )
        else:
            services_with_advisory.append(
                (txcfileattribute.service_code, txcfileattribute.line_names[0])
            )

        task_result = TaskResultsFactory(
            status=TaskResultsStatus.PENDING.value,
            transmodel_txcfileattributes=txcfileattribute,
            checks=check_obj,
        )
        service_pattern = ServicePatternFactory(
            revision=txcfileattribute.revision, line_name=txcfileattribute.line_names[0]
        )
        ServiceFactory(
            revision=txcfileattribute.revision,
            service_code=txcfileattribute.service_code,
            name=txcfileattribute.line_names[0],
            service_patterns=[service_pattern],
            txcfileattributes=txcfileattribute,
        )

        service_pattern_stop = ServicePatternStopFactory(
            service_pattern=service_pattern
        )

        ObservationResultsFactory(
            service_pattern_stop=service_pattern_stop, taskresults=task_result
        )

    lta_objs = LocalAuthority.objects.all()
    otc_service = OTCService.objects.all()

    result = get_timetable_records_require_attention_lta_line_level_length(lta_objs)
    assert result == 8
    assert len(otc_service) == 9
