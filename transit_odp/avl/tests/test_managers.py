import random
from datetime import datetime, timedelta

import pytest
from django.db.models.aggregates import Sum
from factory import Iterator

from transit_odp.avl.constants import (
    AWAITING_REVIEW,
    COMPLIANT,
    LOWER_THRESHOLD,
    MORE_DATA_NEEDED,
    NON_COMPLIANT,
    PARTIALLY_COMPLIANT,
    UNDERGOING,
    UPPER_THRESHOLD,
    VALIDATION_TERMINATED,
)
from transit_odp.avl.factories import (
    AVLSchemaValidationReportFactory,
    AVLValidationReportFactory,
)
from transit_odp.avl.models import AVLValidationReport
from transit_odp.avl.proxies import AVLDataset
from transit_odp.avl.tests.utils import (
    get_awaiting_review_revision,
    get_compliant_revision,
    get_dormant_revision,
    get_feed_down_revision,
    get_non_compliant_revision,
    get_partially_compliant_revision,
    get_undergoing_validation_revision,
)
from transit_odp.organisation.constants import (
    EXPIRED,
    INACTIVE,
    LIVE,
    SUCCESS,
    AVLFeedDown,
    AVLFeedUp,
)
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    OrganisationFactory,
)

pytestmark = pytest.mark.django_db


def test_add_critical_exists_one_day():
    """
    GIVEN that a AVL DatasetRevision has 1 AVL validation report created today
    with one critical error
    WHEN add_critical_exists is annotated on to a dataset
    THEN the dataset.critical_exist should be True
    """
    revision = AVLDatasetRevisionFactory()
    AVLValidationReportFactory(
        created=datetime.now().date(), revision=revision, critical_count=10
    )

    datasets = AVLDataset.objects.add_critical_exists()
    assert datasets.get(id=revision.dataset_id).critical_exists


def test_add_critical_exists_seven_days():
    """
    GIVEN that a AVL DatasetRevision has 7 AVL validation report in the last 7 days
    with one report with one critical error and 6 reports with no errors
    WHEN add_critical_exists is annotated on to a dataset
    THEN the dataset.critical_exist should be True
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    AVLValidationReportFactory(created=today, revision=revision, critical_score=0.6)
    for n in range(1, 7):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(revision=revision, created=date, critical_score=1.0)
    datasets = AVLDataset.objects.add_critical_exists()
    assert datasets.get(id=revision.dataset_id).critical_exists


def test_add_critical_exists_eight_days():
    """
    GIVEN that a AVL DatasetRevision has 8 AVL validation report in the last 8 days
    with the oldest report with one critical error and the 7 most recent reports having
    critical counts of 0
    WHEN add_critical_exists is annotated on to a dataset
    THEN the dataset.critical_exist should be False
    """
    revision = AVLDatasetRevisionFactory()
    total_days = 8
    today = datetime.now().date()
    for n in range(0, total_days):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(revision=revision, created=date, critical_count=0)
    oldest_date = today - timedelta(days=total_days)
    AVLValidationReportFactory(revision=revision, created=oldest_date, critical_count=1)
    datasets = AVLDataset.objects.add_critical_exists()
    assert not datasets.get(id=revision.dataset_id).critical_exists


def test_add_non_critical_exists_one_day():
    """
    GIVEN that a AVL DatasetRevision has 1 AVL validation report created today
    with one non critical error
    WHEN add_non_critical_exists is called
    THEN the dataset.non_critical_exist should be True
    """
    revision = AVLDatasetRevisionFactory()
    AVLValidationReportFactory(
        created=datetime.now().date(), revision=revision, non_critical_score=0.6
    )

    datasets = AVLDataset.objects.add_non_critical_exists()
    assert datasets.get(id=revision.dataset_id).non_critical_exists


def test_add_non_critical_exists_seven_days():
    """
    GIVEN that a AVL DatasetRevision has 7 AVL validation report in the last 7 days
    with one report with one non critical error and 6 reports with no errors
    WHEN add_non_critical_exists is called
    THEN the dataset.non_critical_exist should be True
    """
    revision = AVLDatasetRevisionFactory()

    today = datetime.now().date()
    AVLValidationReportFactory(created=today, revision=revision, non_critical_score=0.6)
    for n in range(1, 7):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision, created=date, non_critical_score=1.0
        )

    datasets = AVLDataset.objects.add_non_critical_exists()
    assert datasets.get(id=revision.dataset_id).non_critical_exists


def test_add_non_critical_exists_eight_days():
    """
    GIVEN that a AVL DatasetRevision has 8 AVL validation report in the last 8 days
    with the oldest report with one non critical error and the 7 most recent reports
    with no errors
    WHEN add_non_critical_exists is called
    THEN the dataset.non_critical_exists should be False
    """
    revision = AVLDatasetRevisionFactory()
    total_days = 8
    today = datetime.now().date()
    for n in range(0, total_days):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision, created=date, non_critical_count=0
        )

    oldest_date = today - timedelta(days=total_days)
    AVLValidationReportFactory(
        revision=revision, created=oldest_date, non_critical_count=1
    )

    datasets = AVLDataset.objects.add_non_critical_exists()
    assert not datasets.get(id=revision.dataset_id).non_critical_exists


def test_undergoing_validation_scenario():
    """
    GIVEN that an AVL dataset has 7 or less reports with no errors
    WHEN add_avl_compliance_status is called
    THEN the dataset will have an avl_compliance of "Undergoing validation"
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    total_reports = 7
    for n in range(0, total_reports):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            created=date,
            critical_score=1.0,
            non_critical_score=1.0,
            critical_count=0,
            non_critical_count=0,
        )
    datasets = AVLDataset.objects.add_avl_compliance_status()
    dataset = datasets.first()
    assert dataset.avl_report_count == total_reports
    assert dataset.avl_compliance == UNDERGOING


def test_awaiting_review_scenario():
    """
    GIVEN that an AVL dataset has 7 or less reports with at least one having issues
    WHEN add_avl_compliance_status is called
    THEN the dataset will have an avl_compliance of "Awaiting publisher review"
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    total_reports = 7
    AVLValidationReportFactory(
        revision=revision, created=today, critical_count=20, non_critical_count=10
    )
    for n in range(1, total_reports):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            created=date,
            critical_score=1.0,
            non_critical_score=1.0,
            critical_count=0,
            non_critical_count=0,
        )

    datasets = AVLDataset.objects.add_avl_compliance_status()
    dataset = datasets.first()
    assert dataset.avl_report_count == total_reports
    assert dataset.avl_compliance == AWAITING_REVIEW


def test_partially_compliant_scenario():
    """
    GIVEN that an AVL dataset has more than 7 reports with an avg_critical_score greater
    than the UPPER_THRESHOLD and an avg_non_critical_score less than the UPPER_THRESHOLD
    WHEN add_avl_compliance_status is called
    THEN the dataset will have an avl_compliance of "Partially compliant"
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    total_reports = 8
    for n in range(0, total_reports):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            created=date,
            non_critical_score=UPPER_THRESHOLD - 0.1,
            critical_score=UPPER_THRESHOLD + 0.1,
            vehicle_activity_count=100,
        )

    datasets = AVLDataset.objects.add_avl_compliance_status()
    dataset = datasets.first()
    assert dataset.avl_report_count == total_reports
    assert dataset.avl_compliance == PARTIALLY_COMPLIANT


def test_compliant_scenario():
    """
    GIVEN that an AVL dataset has more than 7 reports with no report having an error
    WHEN add_avl_compliance_status is called
    THEN the dataset will have an avl_compliance of "Compliant"
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    total_reports = 8
    for n in range(0, total_reports):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision, created=date, critical_score=1.0, non_critical_score=1.0
        )

    datasets = AVLDataset.objects.add_avl_compliance_status()
    dataset = datasets.first()
    assert dataset.avl_report_count == total_reports
    assert dataset.avl_compliance == COMPLIANT


def test_validation_terminated_scenario():
    """
    GIVEN that an AVL dataset has more than 7 reports with no report having an error but status is INACTIVE
    WHEN add_avl_compliance_status is called
    THEN the dataset will have an avl_compliance of "Validation terminated"
    """
    revision = AVLDatasetRevisionFactory(status=INACTIVE)
    today = datetime.now().date()
    total_reports = 8
    for n in range(0, total_reports):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision, created=date, critical_score=1.0, non_critical_score=1.0
        )

    datasets = AVLDataset.objects.add_avl_compliance_status()
    dataset = datasets.first()
    assert dataset.avl_report_count == total_reports
    assert dataset.avl_compliance == VALIDATION_TERMINATED


def test_non_compliant_scenario():
    """
    GIVEN that an AVL dataset has more than 7 reports with an avg critical score
    of less than the UPPER_THRESHOLD
    WHEN add_avl_compliance_status is called
    THEN the dataset will have an avl_compliance of "Non-Compliant"
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    total_reports = 8
    for n in range(0, total_reports):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            created=date,
            critical_score=UPPER_THRESHOLD - 0.1,
            non_critical_score=UPPER_THRESHOLD + 0.1,
        )

    datasets = AVLDataset.objects.add_avl_compliance_status()
    dataset = datasets.first()
    assert dataset.avl_report_count == total_reports
    assert dataset.avl_compliance == NON_COMPLIANT


def test_more_data_needed_scenario():
    """
    GIVEN that an AVL dataset has more than 7 reports with 0 vehicle_activity_count
    WHEN add_avl_compliance_status is called
    THEN the dataset will have an avl_compliance of "More data needed"
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    total_reports = 8
    for n in range(0, total_reports):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            created=date,
            vehicle_activity_count=0,
            file=None,
        )

    datasets = AVLDataset.objects.add_avl_compliance_status()
    dataset = datasets.first()
    assert dataset.avl_report_count == total_reports
    assert dataset.avl_compliance == MORE_DATA_NEEDED


def test_non_compliant_scenario_lower_threshold():
    """
    GIVEN that an AVL dataset has more than 7 reports with an avg critical score
    of greater than the UPPER_THRESHOLD
    WHEN a new report with critical score less than the lower threshold is created and
    add_avl_compliance_status is called
    THEN the dataset will have an avl_compliance of "Non-Compliant"
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    AVLValidationReportFactory(
        revision=revision,
        created=today,
        critical_score=LOWER_THRESHOLD - 0.1,
        non_critical_score=UPPER_THRESHOLD + 0.1,
    )

    total_reports = 8
    for n in range(1, total_reports):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            created=date,
            critical_score=UPPER_THRESHOLD + 0.1,
            non_critical_score=UPPER_THRESHOLD + 0.1,
        )
    datasets = AVLDataset.objects.add_avl_compliance_status()
    dataset = datasets.first()
    assert dataset.avl_report_count == total_reports
    assert dataset.avl_compliance == NON_COMPLIANT


def test_critical_weighted_average():
    """
    GIVEN AVLValidationReports with critical_scores and vehicle_activity_counts
    WHEN add_weighted_critical_score is called on an AVLDataset
    THEN the correct avg_critical_score should be annotated on the AVLDataset
    """
    revision = AVLDatasetRevisionFactory()
    total_reports = 8
    today = datetime.now().date()
    for n in range(0, total_reports):
        score = random.random()
        vehicle_count = random.randint(1, 100)
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            created=date,
            critical_score=score,
            vehicle_activity_count=vehicle_count,
        )
    datasets = AVLDataset.objects.add_weighted_critical_score()
    dataset = datasets.last()

    last_week = today - timedelta(days=7)
    reports = AVLValidationReport.objects.filter(
        revision_id=revision.id, created__gt=last_week
    )
    assert reports.count() == 7
    total_vehicles = reports.aggregate(total=Sum("vehicle_activity_count"))["total"]
    score_counts = reports.values_list("critical_score", "vehicle_activity_count")
    expected = sum(score * count for score, count in score_counts) / total_vehicles
    assert pytest.approx(dataset.avg_critical_score, 0.0001) == expected


def test_non_critical_weighted_average():
    """
    GIVEN AVLValidationReports with non_critical_scores and vehicle_activity_counts
    WHEN add_weighted_non_critical_score is called on an AVLDataset
    THEN the correct avg_non_critical_score should be annotated on the AVLDataset
    """
    revision = AVLDatasetRevisionFactory()
    total_reports = 8
    today = datetime.now().date()
    for n in range(0, total_reports):
        score = random.random()
        vehicle_count = random.randint(1, 100)
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            created=date,
            non_critical_score=score,
            vehicle_activity_count=vehicle_count,
        )
    datasets = AVLDataset.objects.add_weighted_non_critical_score()
    dataset = datasets.last()

    last_week = today - timedelta(days=7)
    reports = AVLValidationReport.objects.filter(
        revision_id=revision.id, created__gt=last_week
    )

    total_vehicles = reports.aggregate(total=Sum("vehicle_activity_count"))["total"]
    score_counts = reports.values_list("non_critical_score", "vehicle_activity_count")
    expected = sum(score * count for score, count in score_counts) / total_vehicles
    assert pytest.approx(dataset.avg_non_critical_score, 0.0001) == expected


def test_has_schema_violations_no_violations():
    """
    GIVEN An AVLDatasetRevision with no AVLSchemaValidationReports
    WHEN add_has_schema_violation_reports is called on an AVLDataset
    THEN has_schema_violations is set to False
    """
    AVLDatasetRevisionFactory()
    datasets = AVLDataset.objects.add_has_schema_violation_reports()
    dataset = datasets.last()
    assert not dataset.has_schema_violations


def test_has_schema_violations_with_violations():
    """
    GIVEN An AVLDatasetRevision with 1 AVLSchemaValidationReport
    WHEN add_has_schema_violation_reports is called on an AVLDataset
    THEN has_schema_violations is set to True
    """
    AVLSchemaValidationReportFactory()
    datasets = AVLDataset.objects.add_has_schema_violation_reports()
    dataset = datasets.last()
    assert dataset.has_schema_violations


def test_add_first_error_date_no_errors():
    """
    GIVEN An AVL dataset with perfect AVLValidationReport
    WHEN add_first_error_date is called
    THEN first_error_date should be None
    """
    revision = AVLDatasetRevisionFactory()
    start = datetime.now().date()

    report_count = 4
    for n in range(report_count):
        created = start - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            critical_count=0,
            non_critical_count=0,
            critical_score=1.0,
            non_critical_score=1.0,
            created=created,
        )

    datasets = AVLDataset.objects.add_first_error_date()
    dataset = datasets.first()

    assert dataset.first_error_date is None


def test_add_first_error_date_critical():
    """
    GIVEN An AVL dataset with perfect AVLValidationReport for the first 4 days and then
    errors on the 5th day
    WHEN add_first_error_date is called
    THEN first_error_date should return the date of the 5th day
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    report_count = 4
    start = today - timedelta(days=report_count + 1)
    for n in range(report_count):
        created = start + timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            critical_count=0,
            non_critical_count=0,
            critical_score=1.0,
            non_critical_score=1.0,
            created=created,
        )

    AVLValidationReportFactory(
        revision=revision,
        critical_count=1,
        non_critical_count=0,
        critical_score=1.0,
        non_critical_score=1.0,
        created=today,
    )

    datasets = AVLDataset.objects.add_first_error_date()
    dataset = datasets.first()

    assert dataset.first_error_date == today


def test_add_first_error_date_non_critical():
    """
    GIVEN An AVL dataset with perfect AVLValidationReport for the first 4 days and then
    errors on the 5th day
    WHEN add_first_error_date is called
    THEN first_error_date should return the date of the 5th day
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    report_count = 4
    start = today - timedelta(days=report_count + 1)
    for n in range(report_count):
        AVLValidationReportFactory(
            revision=revision,
            critical_count=0,
            non_critical_count=0,
            critical_score=1.0,
            non_critical_score=1.0,
            created=start + timedelta(days=n),
        )

    AVLValidationReportFactory(
        revision=revision,
        critical_count=0,
        non_critical_count=1,
        critical_score=1.0,
        non_critical_score=1.0,
        created=today,
    )

    datasets = AVLDataset.objects.add_first_error_date()
    dataset = datasets.first()

    assert dataset.first_error_date == today


@pytest.mark.parametrize(
    ("first_report_created_ago", "expected"),
    [(None, False), (0, False), (1, False), (6, False), (7, True), (8, True)],
)
def test_add_is_post_seven_days(first_report_created_ago: int, expected: bool):
    """
    GIVEN an AVLDataset with one report older than `first_report_created_ago` days
    WHEN add_is_post_seven_days is called
    THEN the attribute post_seven_days should be `expected`
    """
    revision = AVLDatasetRevisionFactory()

    if first_report_created_ago is not None:
        today = datetime.now().date()
        AVLValidationReportFactory(
            revision=revision,
            critical_count=0,
            non_critical_count=1,
            critical_score=1.0,
            non_critical_score=1.0,
            created=today - timedelta(days=first_report_created_ago),
        )

    datasets = AVLDataset.objects.add_is_post_seven_days()
    dataset = datasets.first()

    assert dataset.post_seven_days == expected


def test_search_across_nocs_returns_distinct_datasets():
    org1 = OrganisationFactory(nocs=["org11", "org12"])
    org2 = OrganisationFactory(nocs=["org21", "org22"])

    AVLDatasetRevisionFactory(dataset__organisation=org1)
    AVLDatasetRevisionFactory(dataset__organisation=org2)

    datasets = AVLDataset.objects.search("org")
    assert datasets.count() == 2, "check does not return duplicate orgs then datasets"


def test_search_org_name():
    org1 = OrganisationFactory(name="buscompany", nocs=2)
    org2 = OrganisationFactory(nocs=2)

    AVLDatasetRevisionFactory(dataset__organisation=org1, is_published=True)
    AVLDatasetRevisionFactory(dataset__organisation=org2, is_published=True)
    AVLDatasetRevisionFactory(dataset__organisation=org2, is_published=True)

    datasets = AVLDataset.objects.search("buscompany")
    assert datasets.count() == 1


def test_search_avl_description():
    org1 = OrganisationFactory(nocs=2)
    org2 = OrganisationFactory(nocs=2)

    AVLDatasetRevisionFactory(
        description="a test datafeed", dataset__organisation=org1, is_published=True
    )
    AVLDatasetRevisionFactory(dataset__organisation=org2, is_published=True)
    AVLDatasetRevisionFactory(dataset__organisation=org2, is_published=True)

    datasets = AVLDataset.objects.search("datafeed")
    assert datasets.count() == 1


def test_get_datafeeds_to_validate():
    """
    GIVEN The database contains a mixture of published and unpublished data feeds
    with statuses of LIVE, SUCCESS, EXPIRED and INACTIVE.
    THEN only the LIVE, published feeds are returned.
    WHEN get_datafeeds_to_validate is called.
    """
    avl_statuses = Iterator([AVLFeedUp, AVLFeedDown])
    live_feeds = 10
    AVLDatasetRevisionFactory.create_batch(
        live_feeds, status=LIVE, dataset__avl_feed_status=avl_statuses
    )
    AVLDatasetRevisionFactory(is_published=True, status=INACTIVE)
    AVLDatasetRevisionFactory(is_published=False, status=SUCCESS)
    AVLDatasetRevisionFactory(is_published=True, status=EXPIRED)
    feeds = AVLDataset.objects.get_datafeeds_to_validate()

    assert feeds.count() == live_feeds


def test_needs_attention_count():
    """
    GIVEN a mixture of dataset compliance statuses
    WHEN calling `get_needs_attention_count`
    THEN the correct number of datasets that need attention is returned.
    """
    compliant_count = 3
    for _ in range(compliant_count):
        get_compliant_revision()

    undergoing_review_count = 5
    for _ in range(undergoing_review_count):
        get_undergoing_validation_revision()

    expected = 0
    dormant_count = 4
    for _ in range(dormant_count):
        get_dormant_revision()
    expected += dormant_count

    non_compliant_count = 5
    for _ in range(non_compliant_count):
        get_non_compliant_revision()
    expected += non_compliant_count

    partially_compliant_count = 2
    for _ in range(partially_compliant_count):
        get_partially_compliant_revision()
    expected += partially_compliant_count

    awaiting_review_count = 3
    for _ in range(awaiting_review_count):
        get_awaiting_review_revision()
    expected += awaiting_review_count

    feed_down = 2
    for _ in range(feed_down):
        get_feed_down_revision()
    expected += feed_down

    actual = AVLDataset.objects.get_needs_attention_count()

    assert actual == expected
