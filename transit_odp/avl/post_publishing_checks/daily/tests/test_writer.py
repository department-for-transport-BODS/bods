from datetime import datetime

from transit_odp.avl.post_publishing_checks.daily.writer import (
    PostPublishingResultsJsonWriter,
)
from transit_odp.avl.post_publishing_checks.daily.results import ValidationResult
from transit_odp.avl.post_publishing_checks.constants import (
    ErrorCode,
    TransXChangeField,
    SirivmField,
)


def test_compile_error_data():

    validation_result = ValidationResult()
    validation_result.errors_code[ErrorCode.CODE_1_2.name] = True
    validation_result.set_transxchange_attribute(TransXChangeField.DATASET_ID, 12)
    validation_result.set_transxchange_attribute(TransXChangeField.FILENAME, "5410.xml")
    validation_result.set_transxchange_attribute(
        TransXChangeField.MODIFICATION_DATE, "2022-12-07T11:35:14+00:00"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.REVISION_NUMBER, "64"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_START_DATE, "2023-01-08"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_END_DATE, None
    )
    validation_result.set_transxchange_attribute(
        SirivmField.DATED_VEHICLE_JOURNEY_REF, "22"
    )
    validation_result.set_transxchange_attribute(SirivmField.LINE_REF, "22")
    validation_result.set_transxchange_attribute(
        SirivmField.RECORDED_AT_TIME, "2024-06-04T11:24:31+00:00"
    )

    post_publishing_check_report = PostPublishingResultsJsonWriter(
        activity_date=datetime.now(), feed_id=14
    )

    results = post_publishing_check_report.compile_error_data([validation_result])

    expected_keys_error_code_1_2 = [
        "Dataset ID",
        "Filename",
        "Modification date",
        "Revision number",
        "Operation period start date",
        "Operating period end date",
        "Dated Vehicle Journey Ref",
        "Line Name",
        "Recorded at time",
    ]
    assert results["CODE_1_2"] is not None
    for list_item in results["CODE_1_2"]:
        for key, _ in list_item.items():
            assert key in expected_keys_error_code_1_2

    validation_result = ValidationResult()
    validation_result.errors_code[ErrorCode.CODE_2_1.name] = True
    validation_result.set_transxchange_attribute(TransXChangeField.DATASET_ID, 12)
    validation_result.set_transxchange_attribute(TransXChangeField.FILENAME, "5410.xml")
    validation_result.set_transxchange_attribute(
        TransXChangeField.MODIFICATION_DATE, "2022-12-07T11:35:14+00:00"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.REVISION_NUMBER, "64"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_START_DATE, "2023-01-08"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_END_DATE, None
    )
    validation_result.set_transxchange_attribute(
        SirivmField.DATED_VEHICLE_JOURNEY_REF, "22"
    )
    validation_result.set_transxchange_attribute(SirivmField.LINE_REF, "22")
    validation_result.set_transxchange_attribute(
        SirivmField.RECORDED_AT_TIME, "2024-06-04T11:24:31+00:00"
    )

    post_publishing_check_report = PostPublishingResultsJsonWriter(
        activity_date=datetime.now(), feed_id=14
    )

    results = post_publishing_check_report.compile_error_data([validation_result])

    expected_keys_error_code_2_1 = [
        "Dataset ID",
        "Filename",
        "Modification date",
        "Revision number",
        "Operation period start date",
        "Operating period end date",
        "Dated Vehicle Journey Ref",
        "Line Name",
        "Recorded at time",
    ]
    assert results["CODE_2_1"] is not None
    for list_item in results["CODE_2_1"]:
        for key, _ in list_item.items():
            assert key in expected_keys_error_code_2_1

    validation_result = ValidationResult()
    validation_result.errors_code[ErrorCode.CODE_3_1.name] = True
    validation_result.set_transxchange_attribute(TransXChangeField.DATASET_ID, 12)
    validation_result.set_transxchange_attribute(TransXChangeField.FILENAME, "5410.xml")
    validation_result.set_transxchange_attribute(
        TransXChangeField.MODIFICATION_DATE, "2022-12-07T11:35:14+00:00"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.REVISION_NUMBER, "64"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_START_DATE, "2023-01-08"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_END_DATE, None
    )
    validation_result.set_transxchange_attribute(
        SirivmField.DATED_VEHICLE_JOURNEY_REF, "22"
    )
    validation_result.set_transxchange_attribute(SirivmField.LINE_REF, "22")
    validation_result.set_transxchange_attribute(
        SirivmField.RECORDED_AT_TIME, "2024-06-04T11:24:31+00:00"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.JOURNEY_CODE, "journey code 1"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PROFILES, ["operating_profile_string"]
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.SERVICE_CODE, "service code"
    )

    post_publishing_check_report = PostPublishingResultsJsonWriter(
        activity_date=datetime.now(), feed_id=14
    )

    results = post_publishing_check_report.compile_error_data([validation_result])

    expected_keys_error_code_3_1 = [
        "Dataset ID",
        "Filename",
        "Modification date",
        "Revision number",
        "Operation period start date",
        "Operating period end date",
        "Dated Vehicle Journey Ref",
        "Line Name",
        "Recorded at time",
        "Journey Code",
        "Operating Profile",
        "Service Code",
    ]
    assert results["CODE_3_1"] is not None
    for list_item in results["CODE_3_1"]:
        for key, _ in list_item.items():
            assert key in expected_keys_error_code_3_1

    validation_result = ValidationResult()
    validation_result.errors_code[ErrorCode.CODE_5_1.name] = True
    validation_result.set_transxchange_attribute(TransXChangeField.DATASET_ID, 12)
    validation_result.set_transxchange_attribute(TransXChangeField.FILENAME, "5410.xml")
    validation_result.set_transxchange_attribute(
        TransXChangeField.MODIFICATION_DATE, "2022-12-07T11:35:14+00:00"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.REVISION_NUMBER, "64"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_START_DATE, "2023-01-08"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_END_DATE, None
    )
    validation_result.set_transxchange_attribute(
        SirivmField.DATED_VEHICLE_JOURNEY_REF, "22"
    )
    validation_result.set_transxchange_attribute(SirivmField.LINE_REF, "22")
    validation_result.set_transxchange_attribute(
        SirivmField.RECORDED_AT_TIME, "2024-06-04T11:24:31+00:00"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.JOURNEY_CODE, "journey code 1"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PROFILES, ["operating_profile_string"]
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.SERVICE_CODE, "service code"
    )

    post_publishing_check_report = PostPublishingResultsJsonWriter(
        activity_date=datetime.now(), feed_id=14
    )

    results = post_publishing_check_report.compile_error_data([validation_result])

    expected_keys_error_code_5_1 = [
        "Dataset ID",
        "Filename",
        "Modification date",
        "Revision number",
        "Operation period start date",
        "Operating period end date",
        "Dated Vehicle Journey Ref",
        "Line Name",
        "Recorded at time",
        "Journey Code",
        "Operating Profile",
        "Service Code",
        "LineRef",
    ]
    assert results["CODE_5_1"] is not None
    for list_item in results["CODE_5_1"]:
        for key, _ in list_item.items():
            assert key in expected_keys_error_code_5_1

    validation_result = ValidationResult()
    validation_result.errors_code[ErrorCode.CODE_6_2_A.name] = True
    validation_result.set_transxchange_attribute(TransXChangeField.DATASET_ID, 12)
    validation_result.set_transxchange_attribute(TransXChangeField.FILENAME, "5410.xml")
    validation_result.set_transxchange_attribute(
        TransXChangeField.MODIFICATION_DATE, "2022-12-07T11:35:14+00:00"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.REVISION_NUMBER, "64"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_START_DATE, "2023-01-08"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_END_DATE, None
    )
    validation_result.set_transxchange_attribute(
        SirivmField.DATED_VEHICLE_JOURNEY_REF, "22"
    )
    validation_result.set_transxchange_attribute(SirivmField.LINE_REF, "22")
    validation_result.set_transxchange_attribute(
        SirivmField.RECORDED_AT_TIME, "2024-06-04T11:24:31+00:00"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.SERVICE_ORGANISATION_DETAILS, [{}]
    )

    post_publishing_check_report = PostPublishingResultsJsonWriter(
        activity_date=datetime.now(), feed_id=14
    )

    results = post_publishing_check_report.compile_error_data([validation_result])

    expected_keys_error_code_6_2_A = [
        "Dataset ID",
        "Filename",
        "Modification date",
        "Revision number",
        "Operation period start date",
        "Operating period end date",
        "Dated Vehicle Journey Ref",
        "Line Name",
        "Recorded at time",
        "Journey Code",
        "Operating Profile",
        "Serviced organisation for that journey",
        "Serviced organisation operating on that day",
        "Service Code",
    ]
    assert results["CODE_6_2_A"] is not None
    for list_item in results["CODE_6_2_A"]:
        for key, _ in list_item.items():
            assert key in expected_keys_error_code_6_2_A

    validation_result = ValidationResult()
    validation_result.errors_code[ErrorCode.CODE_6_2_B.name] = True
    validation_result.set_transxchange_attribute(TransXChangeField.DATASET_ID, 12)
    validation_result.set_transxchange_attribute(TransXChangeField.FILENAME, "5410.xml")
    validation_result.set_transxchange_attribute(
        TransXChangeField.MODIFICATION_DATE, "2022-12-07T11:35:14+00:00"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.REVISION_NUMBER, "64"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_START_DATE, "2023-01-08"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.OPERATING_PERIOD_END_DATE, None
    )
    validation_result.set_transxchange_attribute(
        SirivmField.DATED_VEHICLE_JOURNEY_REF, "22"
    )
    validation_result.set_transxchange_attribute(SirivmField.LINE_REF, "22")
    validation_result.set_transxchange_attribute(
        SirivmField.RECORDED_AT_TIME, "2024-06-04T11:24:31+00:00"
    )
    validation_result.set_transxchange_attribute(
        TransXChangeField.SERVICE_ORGANISATION_DETAILS, [{}]
    )

    post_publishing_check_report = PostPublishingResultsJsonWriter(
        activity_date=datetime.now(), feed_id=14
    )

    results = post_publishing_check_report.compile_error_data([validation_result])

    expected_keys_error_code_6_2_B = [
        "Dataset ID",
        "Filename",
        "Modification date",
        "Revision number",
        "Operation period start date",
        "Operating period end date",
        "Dated Vehicle Journey Ref",
        "Line Name",
        "Recorded at time",
        "Journey Code",
        "Operating Profile",
        "Serviced organisation for that journey",
        "Serviced organisation operating on that day",
        "Service Code",
    ]
    assert results["CODE_6_2_B"] is not None
    for list_item in results["CODE_6_2_B"]:
        for key, _ in list_item.items():
            assert key in expected_keys_error_code_6_2_B
