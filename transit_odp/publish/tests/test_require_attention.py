import random
from datetime import date, datetime

import pytest
from freezegun import freeze_time
from waffle.testutils import override_flag

from transit_odp.dqs.constants import Level, TaskResultsStatus
from transit_odp.dqs.factories import (
    ChecksFactory,
    ObservationResultsFactory,
    TaskResultsFactory,
)
from transit_odp.fares.factories import (
    DataCatalogueMetaDataFactory,
    FaresMetadataFactory,
)
from transit_odp.fares_validator.factories import FaresValidationResultFactory
from transit_odp.organisation.factories import (
    ConsumerFeedbackFactory,
    FaresDatasetRevisionFactory,
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models.data import TXCFileAttributes
from transit_odp.publish.requires_attention import (
    evaluate_fares_staleness,
    get_dq_critical_observation_services_map,
    get_fares_compliance_status,
    get_fares_dataset_map,
    get_fares_published_status,
    get_fares_requires_attention,
    get_fares_timeliness_status,
    is_fares_stale,
)
from transit_odp.transmodel.factories import (
    ServiceFactory,
    ServicePatternFactory,
    ServicePatternStopFactory,
)

pytestmark = pytest.mark.django_db


@override_flag("dqs_require_attention", active=True)
@override_flag("is_specific_feedback", active=True)
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


def test_get_fares_dataset_map():
    """
    function to test functionality of get_fares_dataset_map()
    """
    national_operator_code = ["BLAC", "LNUD"]
    organisation = OrganisationFactory(
        licence_required=True, nocs=national_operator_code
    )

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
        random_number = random.randint(0, 1)
        txcfileattributes.append(
            TXCFileAttributesFactory(
                service_code=service["service_code"],
                line_names=service["line_name"],
                national_operator_code=national_operator_code[random_number],
            )
        )

    txcfileattributes = TXCFileAttributes.objects.add_split_linenames().all()
    txcfileattributes_map = {}
    for txcfileattribute in txcfileattributes:
        txcfileattributes_map[txcfileattribute.service_code] = txcfileattribute

    fares_revision = FaresDatasetRevisionFactory(dataset__organisation=organisation)
    faresmetadata = FaresMetadataFactory(
        revision=fares_revision, num_of_fare_products=2
    )
    DataCatalogueMetaDataFactory(
        fares_metadata=faresmetadata,
        fares_metadata__revision__is_published=True,
        line_name=[":::L1", ":::L2", ":::L3"],
        line_id=[":::L1", ":::L2", ":::L3"],
        national_operator_code=national_operator_code,
        valid_from=datetime(2024, 12, 12),
        valid_to=datetime(2025, 1, 12),
    )
    DataCatalogueMetaDataFactory(
        fares_metadata=faresmetadata,
        fares_metadata__revision__is_published=True,
        line_name=[":::L1", ":::L2", ":::L3"],
        line_id=[":::L1", ":::L2", ":::L3"],
        national_operator_code=national_operator_code,
        valid_from=datetime(2025, 1, 12),
        valid_to=datetime(2099, 2, 12),
    )
    DataCatalogueMetaDataFactory(
        fares_metadata=faresmetadata,
        fares_metadata__revision__is_published=True,
        line_name=[":::L1", ":::L2", ":::L3"],
        line_id=[":::L1", ":::L2", ":::L3"],
        national_operator_code=["SR", "BR"],
    )
    FaresValidationResultFactory(revision=fares_revision, count=5)

    result = get_fares_dataset_map(txc_map=txcfileattributes_map)
    assert (
        result[
            (result["national_operator_code"] == "LNUD") & (result["line_name"] == "L1")
        ]["valid_from"]
        == "2025-01-12"
    ).all()
    assert (
        result[
            (result["national_operator_code"] == "BLAC") & (result["line_name"] == "L2")
        ]["valid_from"]
        == "2025-01-12"
    ).all()
    assert (
        result[
            (result["national_operator_code"] == "LNUD") & (result["line_name"] == "L3")
        ]["valid_from"]
        == "2025-01-12"
    ).all()

    assert (
        result[
            (result["national_operator_code"] == "LNUD") & (result["line_name"] == "L1")
        ]["valid_to"]
        == "2099-02-12"
    ).all()
    assert (
        result[
            (result["national_operator_code"] == "BLAC") & (result["line_name"] == "L2")
        ]["valid_to"]
        == "2099-02-12"
    ).all()
    assert (
        result[
            (result["national_operator_code"] == "LNUD") & (result["line_name"] == "L3")
        ]["valid_to"]
        == "2099-02-12"
    ).all()


@freeze_time("04/02/2025")
@pytest.mark.parametrize(
    "operating_period_end_date, last_updated, expected_result",
    [
        (
            date(2025, 1, 19),
            date(2023, 1, 2),
            (True, True),
        ),
        (
            date(2025, 1, 19),
            date(2025, 1, 2),
            (True, False),
        ),
        (
            date(2025, 6, 20),
            date(2023, 1, 2),
            (False, True),
        ),
        (
            date(2025, 6, 20),
            date(2025, 1, 25),
            (False, False),
        ),
        (
            None,
            date(2025, 1, 2),
            (False, False),
        ),
    ],
)
def test_evaluate_fares_staleness(
    operating_period_end_date, last_updated, expected_result
):
    """
    Test for evaluate_fares_staleness function.
    """
    staleness_function_result = evaluate_fares_staleness(
        operating_period_end_date, last_updated
    )

    assert staleness_function_result == expected_result


@freeze_time("04/02/2025")
@pytest.mark.parametrize(
    "operating_period_end_date, last_updated, expected_result",
    [
        (
            date(2025, 1, 19),
            date(2023, 1, 2),
            True,
        ),
        (
            date(2025, 1, 19),
            date(2025, 1, 2),
            True,
        ),
        (
            date(2025, 6, 20),
            date(2023, 1, 2),
            True,
        ),
        (
            date(2025, 6, 20),
            date(2025, 1, 2),
            False,
        ),
    ],
)
def test_is_fares_stale(operating_period_end_date, last_updated, expected_result):
    """
    Test for is_fares_stale function.
    """
    is_fares_stale_function_result = is_fares_stale(
        operating_period_end_date, last_updated
    )

    assert is_fares_stale_function_result == expected_result


@pytest.mark.parametrize(
    "fares_dataset_id, expected_result",
    [
        (
            12,
            "Published",
        ),
        (
            None,
            "Unpublished",
        ),
    ],
)
def test_get_fares_published_status(fares_dataset_id, expected_result):
    """
    Test for get_fares_published_status function.
    """
    fares_published_status = get_fares_published_status(fares_dataset_id)

    assert fares_published_status == expected_result


@pytest.mark.parametrize(
    "is_fares_compliant, expected_result",
    [
        (
            True,
            "Compliant",
        ),
        (
            False,
            "Non compliant",
        ),
    ],
)
def test_get_fares_compliance_status(is_fares_compliant, expected_result):
    """
    Test for get_fares_compliance_status function.
    """
    fares_compliance_status_status = get_fares_compliance_status(is_fares_compliant)

    assert fares_compliance_status_status == expected_result


@freeze_time("04/02/2025")
@pytest.mark.parametrize(
    "valid_to, last_updated_date, expected_result",
    [
        (
            date(2025, 1, 19),
            date(2023, 1, 2),
            "42 day look ahead is incomplete",
        ),
        (
            date(2025, 1, 19),
            date(2025, 1, 2),
            "42 day look ahead is incomplete",
        ),
        (
            date(2025, 6, 20),
            date(2023, 1, 2),
            "One year old",
        ),
        (
            date(2025, 6, 20),
            date(2025, 1, 2),
            "Not Stale",
        ),
        (
            None,
            None,
            "Not Stale",
        ),
    ],
)
def test_get_fares_timeliness_status(valid_to, last_updated_date, expected_result):
    """
    Test for get_fares_timeliness_status function.
    """
    fares_timeliness_status = get_fares_timeliness_status(valid_to, last_updated_date)

    assert fares_timeliness_status == expected_result


@pytest.mark.parametrize(
    "fares_published_status, fares_timeliness_status, fares_compliance_status, expected_result",
    [
        (
            "Published",
            "Not Stale",
            "Compliant",
            "No",
        ),
        (
            "Published",
            "42 day look ahead is incomplete",
            "Compliant",
            "Yes",
        ),
        (
            "Published",
            "One year old",
            "Compliant",
            "Yes",
        ),
        (
            "Unpublished",
            "42 day look ahead is incomplete",
            "Compliant",
            "Yes",
        ),
        (
            "Unpublished",
            "One year old",
            "Compliant",
            "Yes",
        ),
        (
            "Published",
            "One year old",
            "Non compliant",
            "Yes",
        ),
        (
            "Published",
            "Not Stale",
            "Non compliant",
            "Yes",
        ),
    ],
)
def test_get_fares_requires_attention(
    fares_published_status,
    fares_timeliness_status,
    fares_compliance_status,
    expected_result,
):
    """
    Test for get_fares_requires_attention function.
    """
    fares_requires_attention = get_fares_requires_attention(
        fares_published_status, fares_timeliness_status, fares_compliance_status
    )

    assert fares_requires_attention == expected_result
