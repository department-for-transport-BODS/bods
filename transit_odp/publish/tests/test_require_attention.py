import pytest
from transit_odp.dqs.constants import Level, TaskResultsStatus
from waffle.testutils import override_flag
from transit_odp.organisation.factories import (
    ConsumerFeedbackFactory,
    TXCFileAttributesFactory,
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
