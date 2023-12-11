import json
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests_mock
from django.conf import settings
from freezegun import freeze_time
from mocket import Mocketizer
from mocket.mockhttp import Entry
from requests import RequestException
from requests.exceptions import ConnectionError, ReadTimeout

from transit_odp.avl.dataclasses import Feed
from transit_odp.avl.enums import AVL_FEED_DOWN, AVL_FEED_UP
from transit_odp.avl.factories import (
    AVLValidationReportFactory,
    CAVLValidationTaskResultFactory,
)
from transit_odp.avl.models import AVLSchemaValidationReport, CAVLValidationTaskResult
from transit_odp.avl.tasks import (
    task_create_sirivm_tfl_zipfile,
    task_create_sirivm_zipfile,
    task_monitor_avl_feeds,
    task_run_feed_validation,
    task_validate_avl_feed,
    task_weekly_assimilate_post_publishing_check_reports,
)
from transit_odp.avl.validation.factories import (
    SchemaErrorFactory,
    SchemaValidationResponseFactory,
    ValidationResponseFactory,
    ValidationSummaryFactory,
)
from transit_odp.organisation.constants import INACTIVE, LIVE, AVLType
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetFactory,
    DatasetMetadataFactory,
    DatasetRevisionFactory,
)
from transit_odp.organisation.models import Dataset
from transit_odp.users.constants import DeveloperType, OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db
CAVL_PATH = "transit_odp.avl.tasks.CAVLService"
VALIDATION_PATH = "transit_odp.avl.tasks.get_validation_client"


@patch("transit_odp.avl.tasks.CAVLDataArchive")
@patch("transit_odp.avl.tasks.requests")
def test_task_create_sirivm_zipfile(mrequests, marchive):
    filter_ = marchive.objects.filter.return_value = MagicMock()
    filter_.last.return_value = None
    mresponse = MagicMock(content=b"hello")
    mrequests.get.return_value = mresponse
    task_create_sirivm_zipfile()
    marchive.assert_called_once()

    marchive_obj = MagicMock()
    filter_.last.return_value = marchive_obj
    task_create_sirivm_zipfile()
    marchive_obj.save.assert_called_once_with()


@patch("transit_odp.avl.tasks.CAVLDataArchive")
@patch("transit_odp.avl.tasks.requests")
def test_task_create_sirivm_zipfile_exception(mrequests, marchive):
    mrequests.get.side_effect = RequestException
    task_create_sirivm_zipfile()
    assert not marchive.objects.objects.last.called


@patch("transit_odp.avl.tasks.CAVLDataArchive")
@patch("transit_odp.avl.tasks.requests")
def test_task_create_sirivm_tfl_zipfile(mrequests, marchive):
    filter_ = marchive.objects.filter.return_value = MagicMock()
    filter_.last.return_value = None
    mresponse = MagicMock(content=b"hello")
    mrequests.get.return_value = mresponse
    task_create_sirivm_tfl_zipfile()
    params = mrequests.get.call_args.kwargs["params"]
    assert params["operatorRef"] == "TFLO"
    marchive.assert_called_once()


def test_no_feeds_doesnt_break(mocker):
    data = []
    service = Mock()
    service.get_feeds.return_value = data
    mocker.patch(CAVL_PATH, return_value=service)
    task_monitor_avl_feeds()


def test_inconsistant_api_doesnt_break(mocker):
    """Tests dataset exists in database but not in cavl service"""
    DatasetFactory(dataset_type=AVLType)
    data = []
    service = Mock()
    service.get_feeds.return_value = data
    mocker.patch(CAVL_PATH, return_value=service)
    task_monitor_avl_feeds()


def test_no_change(mocker, mailoutbox):
    """tests cavl service reflects whats in the database"""
    subscribers = UserFactory.create_batch(3, account_type=DeveloperType)
    for user in subscribers:
        # created in post save signal so cant add in factory
        user.settings.notify_avl_unavailable = True
        user.settings.save()

    datasets = DatasetFactory.create_batch(
        3, dataset_type=AVLType, avl_feed_status=AVL_FEED_UP, subscribers=subscribers
    )
    data = []
    for dataset in datasets:
        dataset.contact.settings.notify_avl_unavailable = True
        dataset.contact.settings.save()
        data.append(
            Feed(
                id=dataset.id,
                publisher_id=dataset.contact.id,
                url="www.testurl.com/avl",
                username=dataset.contact.username,
                password="password",
                status=dataset.avl_feed_status,
            )
        )

    service = Mock()
    service.get_feeds.return_value = data
    mocker.patch(CAVL_PATH, return_value=service)
    task_monitor_avl_feeds()
    assert len(mailoutbox) == 0
    assert (
        Dataset.objects.filter(
            dataset_type=AVLType, avl_feed_status=AVL_FEED_DOWN
        ).count()
        == 0
    )


# class TestValidateAVLTask:
#     @pytest.mark.parametrize(
#         "avl_status,expected_status,expected_version",
#         [
#             ("FEED_VALID", "SUCCESS", "2.0"),
#             ("FEED_INVALID", "FAILURE", "0.0"),
#             ("SYSTEM_ERROR", "FAILURE", "0.0"),
#         ],
#     )
#     def test_task_validate_avl_feed(
#         self, avl_status, expected_status, expected_version, settings
#     ):
#         url = "https://cavlvalidation.com"
#         username = "user"
#         password = "pass"
#         Entry.single_register(
#             Entry.POST,
#             f"{settings.CAVL_URL}/validate",
#             body=json.dumps(
#                 {
#                     "version": expected_version,
#                     "status": avl_status,
#                     "url": url,
#                     "username": username,
#                     "password": password,
#                     "created": datetime.now().isoformat(),
#                 }
#             ),
#             headers={"content-type": "application/json"},
#         )

#         revision = DatasetRevisionFactory(
#             username=username, password=password, url_link=url
#         )
#         DatasetMetadataFactory(revision=revision)
#         task_id = uuid.uuid4()
#         CAVLValidationTaskResultFactory(task_id=task_id, revision=revision)
#         with Mocketizer():
#             task_validate_avl_feed(task_id)

#         task = CAVLValidationTaskResult.objects.get(task_id=task_id)
#         assert task.status == expected_status
#         assert task.revision.metadata.schema_version == expected_version


@patch(VALIDATION_PATH)
def test_email_is_not_sent_on_no_errors(get_client, mailoutbox):
    """
    GIVEN an AVL datafeed that has not had any validation performed.
    WHEN the validation service is called and results in a response with no issues
    THEN no emails are sent
    """
    revision = AVLDatasetRevisionFactory()

    summary = ValidationSummaryFactory(
        critical_score=1,
        non_critical_score=1,
        critical_error_count=0,
        non_critical_error_count=0,
    )
    client = Mock()
    client.schema.return_value = SchemaValidationResponseFactory(
        errors=[], timestamp=0, is_valid=True
    )
    client.validate.return_value = ValidationResponseFactory(validation_summary=summary)
    get_client.return_value = client

    assert revision.avl_validation_reports.count() == 0
    task_run_feed_validation(revision.dataset.id)

    assert len(mailoutbox) == 0


@patch(VALIDATION_PATH)
def test_send_pre_seven_days_action_required(get_client, mailoutbox):
    """
    GIVEN an AVL datafeed that has not had any validation performed.
    WHEN the validation service is called and results in a response with a
    critical issue
    THEN an action required email is sent
    """
    revision = AVLDatasetRevisionFactory()

    summary = ValidationSummaryFactory(
        critical_score=0.9, critical_error_count=1, non_critical_error_count=0
    )
    client = Mock()
    client.schema.return_value = SchemaValidationResponseFactory(
        errors=[], timestamp=0, is_valid=True
    )
    client.validate.return_value = ValidationResponseFactory(validation_summary=summary)
    get_client.return_value = client

    assert revision.avl_validation_reports.count() == 0
    task_run_feed_validation(revision.dataset.id)

    assert revision.avl_validation_reports.count() == 1


@patch(VALIDATION_PATH)
def test_send_flagged_non_compliant(get_client, mailoutbox):
    """
    GIVEN an AVL datafeed with 7 days of non-compliant reports
    WHEN a new non-compliant report is returned by the validation service
    THEN a non-compliant email is sent.
    THEN WHEN a non-compliant report is generated on day 8
    THEN no email is sent.
    """
    user = UserFactory(account_type=OrgAdminType)
    user.settings.daily_compliance_check_alert = True
    user.settings.save()
    revision = AVLDatasetRevisionFactory(
        dataset__contact=user, dataset__organisation=user.organisations.first()
    )
    now = datetime.now(tz=timezone.utc).date()
    report_count = 6

    for n in range(1, report_count + 1):
        AVLValidationReportFactory(
            revision=revision,
            critical_score=0.5,
            non_critical_score=0.5,
            created=now - timedelta(days=n),
        )

    client = Mock()
    schema_report = SchemaValidationResponseFactory(errors=[], is_valid=True)
    client.schema.return_value = schema_report

    summary = ValidationSummaryFactory(critical_score=0.5, non_critical_score=0.5)
    client.validate.return_value = ValidationResponseFactory(validation_summary=summary)
    get_client.return_value = client

    task_run_feed_validation(revision.dataset.id)
    assert len(mailoutbox) == 0

    tomorrow = now + timedelta(days=1)
    with freeze_time(tomorrow):
        # Run the validation report for tomorrow
        task_run_feed_validation(revision.dataset.id)

    expected_subject = (
        "SIRI-VM validation: Your feed is flagged to public as Non-compliant"
    )
    assert len(mailoutbox) == 2
    assert mailoutbox[1].subject in expected_subject
    assert "flagged as Non-compliant" in mailoutbox[1].body
    expected_report_count = report_count + 2  # we ran the task twice
    assert revision.avl_validation_reports.count() == expected_report_count
    mailoutbox.clear()

    day_after_tomorrow = now + timedelta(days=2)
    with freeze_time(day_after_tomorrow):
        # Run the validation report for tomorrow
        task_run_feed_validation(revision.dataset.id)
    assert len(mailoutbox) == 0


@patch(VALIDATION_PATH)
def test_send_flagged_as_dormant(get_client, mailoutbox):
    """

    GIVEN an AVL datafeed with with 8 days of empty reports
    WHEN a new empty report is returned by the validation service
    THEN a dormant feed email is sent.
    THEN WHEN a dormant report is generated on day 9
    THEN no email is sent.
    """
    user = UserFactory(account_type=OrgAdminType)
    user.settings.daily_compliance_check_alert = True
    user.settings.save()
    revision = AVLDatasetRevisionFactory(
        dataset__contact=user, dataset__organisation=user.organisations.first()
    )
    report_count = 9
    for n in range(1, report_count):
        AVLValidationReportFactory(
            revision=revision,
            critical_count=0,
            non_critical_count=0,
            critical_score=1,
            non_critical_score=1,
            vehicle_activity_count=0,
            file=None,
            created=datetime.now().date() - timedelta(days=n),
        )

    summary = ValidationSummaryFactory(
        critical_score=1,
        non_critical_score=1,
        total_error_count=0,
        critical_error_count=0,
        non_critical_error_count=0,
        vehicle_activity_count=0,
    )
    client = Mock()
    client.schema.return_value = SchemaValidationResponseFactory(
        errors=[], timestamp=0, is_valid=True
    )
    client.validate.return_value = ValidationResponseFactory(validation_summary=summary)
    get_client.return_value = client

    task_run_feed_validation(revision.dataset.id)

    assert len(mailoutbox) == 0


@patch(VALIDATION_PATH)
def test_send_flagged_major_issue(get_client, mailoutbox):
    """
    GIVEN an AVL datafeed with with 8 days of non-compliant reports
    WHEN a new non-compliant report is returned with a score below the lower threshold
    on day 9
    THEN no email is sent
    """
    user = UserFactory(account_type=OrgAdminType)
    user.settings.daily_compliance_check_alert = True
    user.settings.save()
    revision = AVLDatasetRevisionFactory(
        dataset__contact=user, dataset__organisation=user.organisations.first()
    )

    report_count = 9
    for n in range(1, report_count):
        AVLValidationReportFactory(
            revision=revision,
            critical_score=0.5,
            non_critical_score=0.5,
            created=datetime.now().date() - timedelta(days=n),
        )

    client = Mock()
    summary = ValidationSummaryFactory(critical_score=0.19, non_critical_score=0.5)
    response = ValidationResponseFactory(validation_summary=summary)
    client.schema.return_value = SchemaValidationResponseFactory(
        errors=[], is_valid=True
    )
    client.validate.return_value = response
    get_client.return_value = client

    task_run_feed_validation(revision.dataset.id)

    assert len(mailoutbox) == 0


@patch(VALIDATION_PATH)
def test_send_status_changed_email(get_client, mailoutbox):
    """
    GIVEN an AVL datafeed with with 8 days of compliant reports
    WHEN a new non-compliant report is returned that brings the weighted average
    below the upper threshold
    THEN a non-compliant email is sent
    """
    user = UserFactory(account_type=OrgAdminType)
    user.settings.daily_compliance_check_alert = True
    user.settings.save()
    revision = AVLDatasetRevisionFactory(
        dataset__contact=user, dataset__organisation=user.organisations.first()
    )
    report_count = 9
    for n in range(1, report_count):
        AVLValidationReportFactory(
            revision=revision,
            critical_score=0.7,
            non_critical_score=0.8,
            vehicle_activity_count=10,
            created=datetime.now().date() - timedelta(days=n),
        )

    summary = ValidationSummaryFactory(
        critical_score=0.6, non_critical_score=0.5, vehicle_activity_count=1000
    )
    client = Mock()
    client.schema.return_value = SchemaValidationResponseFactory(
        errors=[], is_valid=True
    )
    client.validate.return_value = ValidationResponseFactory(validation_summary=summary)
    get_client.return_value = client
    task_run_feed_validation(revision.dataset.id)

    expected_subject = "SIRI-VM compliance status changed to Non-compliant"
    assert len(mailoutbox) > 0
    assert mailoutbox[0].subject == expected_subject
    assert "The SIRI-VM compliance status has changed" in mailoutbox[0].body
    assert revision.avl_validation_reports.count() == report_count


@patch("transit_odp.avl.tasks.get_validation_client")
def test_send_schema_validation_passes(get_client, mailoutbox):
    user = UserFactory(account_type=OrgAdminType)
    user.settings.daily_compliance_check_alert = True
    user.settings.save()
    revision = AVLDatasetRevisionFactory(
        dataset__contact=user, dataset__organisation=user.organisations.first()
    )
    summary = ValidationSummaryFactory(
        critical_score=1, non_critical_score=1, vehicle_activity_count=1000
    )
    client = Mock()
    client.schema.return_value = SchemaValidationResponseFactory()
    client.validate.return_value = ValidationResponseFactory(validation_summary=summary)
    get_client.return_value = client

    assert AVLSchemaValidationReport.objects.count() == 0
    task_run_feed_validation(revision.dataset.id)
    assert len(mailoutbox) == 0
    assert AVLSchemaValidationReport.objects.count() == 0


@patch("transit_odp.avl.tasks.get_validation_client")
def test_feed_validation_can_handle_empty_response(get_client):
    user = UserFactory(account_type=OrgAdminType)
    user.settings.daily_compliance_check_alert = True
    user.settings.save()
    revision = AVLDatasetRevisionFactory(
        dataset__contact=user, dataset__organisation=user.organisations.first()
    )
    summary = ValidationSummaryFactory(
        critical_score=1,
        non_critical_score=1,
        total_error_count=0,
        critical_error_count=0,
        non_critical_error_count=0,
        vehicle_activity_count=0,
    )

    client = Mock()
    client.schema.return_value = SchemaValidationResponseFactory(
        is_valid=True, errors=[], timestamp=0
    )
    client.validate.return_value = ValidationResponseFactory(
        packet_count=0, feed_id=revision.dataset_id, validation_summary=summary
    )
    get_client.return_value = client

    assert revision.avl_validation_reports.count() == 0
    task_run_feed_validation(revision.dataset.id)
    assert revision.avl_validation_reports.count() == 1
    report = revision.avl_validation_reports.first()
    assert report is not None
    assert not report.file


@patch("transit_odp.avl.tasks.CAVLService")
@patch("transit_odp.avl.tasks.get_validation_client")
def test_send_schema_validation_fails(get_client, get_cavl, mailoutbox):
    user = UserFactory(account_type=OrgAdminType)
    user.settings.daily_compliance_check_alert = True
    user.settings.save()
    revision = AVLDatasetRevisionFactory(
        dataset__contact=user, dataset__organisation=user.organisations.first()
    )
    errors = SchemaErrorFactory.create_batch(3)
    response = SchemaValidationResponseFactory(is_valid=False, errors=errors)
    client = Mock()
    client.schema.return_value = response
    get_client.return_value = client
    cavl = Mock()
    get_cavl.return_value = cavl

    assert AVLSchemaValidationReport.objects.count() == 0
    task_run_feed_validation(revision.dataset.id)
    revision.refresh_from_db()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Error publishing data feed"
    assert AVLSchemaValidationReport.objects.count() == 1
    assert revision.status == INACTIVE
    cavl.delete_feed.assert_called_once_with(feed_id=revision.dataset_id)


@pytest.mark.parametrize("exception", [ConnectionError, ReadTimeout])
@patch("transit_odp.avl.tasks.get_validation_client")
@requests_mock.Mocker(kw="m")
def test_send_schema_fails_with_request_exceptions(
    get_client, exception, mailoutbox, **kwargs
):
    """
    Simulate common connection problems with the config API
    """
    m = kwargs["m"]
    matcher = re.compile(settings.CAVL_URL)
    m.delete(matcher, exc=exception)
    user = UserFactory(account_type=OrgAdminType)
    revision = AVLDatasetRevisionFactory(
        dataset__contact=user, dataset__organisation=user.organisations.first()
    )
    errors = SchemaErrorFactory.create_batch(3)
    response = SchemaValidationResponseFactory(is_valid=False, errors=errors)
    client = Mock()
    client.schema.return_value = response
    get_client.return_value = client

    assert AVLSchemaValidationReport.objects.count() == 0
    task_run_feed_validation(revision.dataset.id)
    revision.refresh_from_db()
    assert AVLSchemaValidationReport.objects.count() == 0
    assert revision.status == LIVE
    assert len(mailoutbox) == 0


@patch("transit_odp.avl.tasks.get_validation_client")
@requests_mock.Mocker(kw="m")
def test_send_schema_fails_with_502_bad_gateway(get_client, mailoutbox, **kwargs):
    """
    Simulate a bad gateway response from the server.
    """
    m = kwargs["m"]
    matcher = re.compile(settings.CAVL_URL)
    m.delete(
        matcher,
        status_code=HTTPStatus.BAD_GATEWAY,
        json={"message": "Internal server error"},
    )
    user = UserFactory(account_type=OrgAdminType)
    revision = AVLDatasetRevisionFactory(
        dataset__contact=user, dataset__organisation=user.organisations.first()
    )
    errors = SchemaErrorFactory.create_batch(3)
    response = SchemaValidationResponseFactory(is_valid=False, errors=errors)
    client = Mock()
    client.schema.return_value = response
    get_client.return_value = client

    assert AVLSchemaValidationReport.objects.count() == 0
    task_run_feed_validation(revision.dataset.id)
    revision.refresh_from_db()
    assert AVLSchemaValidationReport.objects.count() == 0
    assert revision.status == LIVE
    assert len(mailoutbox) == 0


@freeze_time("2022-05-25")
@pytest.mark.parametrize(
    "start_date,expected_date",
    [("2022-05-24", date(2022, 5, 24)), (None, date(2022, 5, 25))],
)
@patch("transit_odp.avl.tasks.WeeklyReport")
def test_weekly_ppc_report_started_with_correct_date(
    weekly_report_mock: Mock, start_date: str, expected_date: date
):
    task_weekly_assimilate_post_publishing_check_reports(start_date)

    weekly_report_mock.assert_called_once_with(expected_date)
