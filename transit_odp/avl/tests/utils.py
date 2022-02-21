from datetime import datetime, timedelta

from transit_odp.avl.factories import (
    AVLDatasetRevisionFactory,
    AVLValidationReportFactory,
)
from transit_odp.organisation.models import DatasetRevision


def get_avl_revision(
    critical_score: float = 1.0,
    critical_count: int = 1,
    non_critical_score: float = 1.0,
    non_critical_count: int = 1,
    vehicle_activity_count: int = 1,
    report_count: int = 7,
) -> DatasetRevision:
    """
    Returns an AVL DatasetRevision with `report_count` reports.
    """
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    for n in range(0, report_count):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            created=date,
            critical_score=critical_score,
            critical_count=critical_count,
            non_critical_score=non_critical_score,
            non_critical_count=non_critical_count,
            vehicle_activity_count=vehicle_activity_count,
        )
    return revision


def get_dormant_revision() -> DatasetRevision:
    """
    Returns an AVL DatasetRevision with a dormant status.
    """
    critical_score = 1.0
    non_critical_score = 1.0
    report_count = 8
    vehicle_activity_count = 0
    return get_avl_revision(
        critical_score=critical_score,
        non_critical_score=non_critical_score,
        vehicle_activity_count=vehicle_activity_count,
        report_count=report_count,
    )


def get_compliant_revision() -> DatasetRevision:
    """
    Returns an AVL DatasetRevision with a compliant status.
    """
    critical_score = 0.9
    critical_count = 0
    non_critical_score = 0.9
    non_critical_count = 0
    report_count = 8
    vehicle_activity_count = 100
    return get_avl_revision(
        critical_score=critical_score,
        critical_count=critical_count,
        non_critical_score=non_critical_score,
        non_critical_count=non_critical_count,
        vehicle_activity_count=vehicle_activity_count,
        report_count=report_count,
    )


def get_non_compliant_revision() -> DatasetRevision:
    """
    Returns an AVL DatasetRevision with a non-compliant status.
    """

    critical_score = 0.6
    non_critical_score = 0.6
    report_count = 8
    vehicle_activity_count = 100
    return get_avl_revision(
        critical_score=critical_score,
        non_critical_score=non_critical_score,
        vehicle_activity_count=vehicle_activity_count,
        report_count=report_count,
    )


def get_partially_compliant_revision() -> DatasetRevision:
    """
    Returns an AVL DatasetRevision with a partially-compliant status.
    """

    critical_score = 0.9
    non_critical_score = 0.6
    report_count = 8
    vehicle_activity_count = 100
    return get_avl_revision(
        critical_score=critical_score,
        non_critical_score=non_critical_score,
        vehicle_activity_count=vehicle_activity_count,
        report_count=report_count,
    )


def get_awaiting_review_revision():
    """
    Returns an AVL DatasetRevision with an awaiting review status.
    """
    critical_score = 0.6
    non_critical_score = 0.6
    report_count = 4
    vehicle_activity_count = 100
    return get_avl_revision(
        critical_score=critical_score,
        non_critical_score=non_critical_score,
        vehicle_activity_count=vehicle_activity_count,
        report_count=report_count,
    )


def get_undergoing_validation_revision():
    """
    Returns an AVL DatasetRevision with an undergoing validation status.
    """
    critical_score = 1.0
    critical_count = 0
    non_critical_score = 1.0
    non_critical_count = 0
    report_count = 4
    vehicle_activity_count = 100
    return get_avl_revision(
        critical_score=critical_score,
        critical_count=critical_count,
        non_critical_score=non_critical_score,
        non_critical_count=non_critical_count,
        vehicle_activity_count=vehicle_activity_count,
        report_count=report_count,
    )
