from unittest.mock import patch

import pytest

from transit_odp.data_quality.constants import (
    WEIGHTED_OBSERVATIONS,
    CheckBasis,
    IncorrectNocObservation,
)
from transit_odp.dqs.constants import (
    IncorrectStopTypeObservation,
    StopNotInNaptanObservation,
)

from transit_odp.data_quality.etl import TransXChangeDQPipeline
from transit_odp.data_quality.factories.transmodel import (
    DataQualityReportFactory,
    ServicePatternStopFactory,
)
from transit_odp.data_quality.factories.warnings import (
    IncorrectNOCWarningFactory,
)
from transit_odp.data_quality.scoring import (
    AMBER,
    GREEN,
    RED,
    DataQualityCalculator,
    DataQualityCounts,
    DataQualityRAG,
    DQScoreException,
)

pytestmark = pytest.mark.django_db

DQ_COUNTS = DataQualityCounts(
    data_set=1, timing_patterns=15, stops=40, vehicle_journeys=120, lines=2
)
DQC_FROM_REPORT_ID = "transit_odp.data_quality.scoring.DataQualityCounts.from_report_id"
SCORE_TOLERANCE = 0.0001


def score_contribution(warning_count: int, check_basis_count: int, weighting: float):
    """
    Returns the score a particular check will contribute.
    """
    return (1 - warning_count / check_basis_count) * weighting


def test_weightings_add_to_one():
    total_weighting = sum(o.weighting for o in WEIGHTED_OBSERVATIONS)
    expected_score = 1.0
    assert len(WEIGHTED_OBSERVATIONS) == 9
    assert pytest.approx(total_weighting, SCORE_TOLERANCE) == expected_score


@patch(DQC_FROM_REPORT_ID, return_value=DQ_COUNTS)
def test_score_calculation_with_no_observations(DQC: DataQualityCounts):
    """
    Given that there are no observations a score of 1 is calculated.
    """
    calculator = DataQualityCalculator(WEIGHTED_OBSERVATIONS)
    report = DataQualityReportFactory()
    score = calculator.calculate(report_id=report.id)
    expected_score = 1.0
    assert pytest.approx(score, SCORE_TOLERANCE) == expected_score


@patch(DQC_FROM_REPORT_ID, return_value=DQ_COUNTS)
def test_score_calculation_with_data_set_component(from_report_id):
    """
    Given that a report contain a mixture of `data_set` warnings a correct score is
    calculated.

    Possible warnings:
        IncorrectNOCWarning
    """
    report = DataQualityReportFactory()
    expected_score = sum(
        o.weighting
        for o in WEIGHTED_OBSERVATIONS
        if not o.check_basis == CheckBasis.data_set
    )
    data_set_count = 1

    # even if 5 are created the warning should be counted once
    IncorrectNOCWarningFactory.create_batch(5, report=report)
    incorrect_weight = IncorrectNocObservation.weighting
    incorrect_score = score_contribution(1, data_set_count, incorrect_weight)

    expected_score += incorrect_score

    pipeline = TransXChangeDQPipeline(report)
    pipeline.load_summary()
    calculator = DataQualityCalculator(WEIGHTED_OBSERVATIONS)
    score = calculator.calculate(report.id)
    assert pytest.approx(score, SCORE_TOLERANCE) == expected_score


@patch(DQC_FROM_REPORT_ID, return_value=DQ_COUNTS)
def test_score_calculation_lines_component(from_report_id):
    """
    Test that the score is calculated correctly with one or more observations
    that are concerned with the `lines` feature.

    Possible warnings:
        LineMissingBlockIDWarning
    """
    report = DataQualityReportFactory()
    line_count = DQ_COUNTS.lines
    expected_score = sum(
        o.weighting
        for o in WEIGHTED_OBSERVATIONS
        if not o.check_basis == CheckBasis.lines
    )

    pipeline = TransXChangeDQPipeline(report)
    pipeline.load_summary()
    calculator = DataQualityCalculator(WEIGHTED_OBSERVATIONS)
    score = calculator.calculate(report.id)
    assert pytest.approx(score, SCORE_TOLERANCE) == expected_score


@patch(DQC_FROM_REPORT_ID)
def test_score_calculation_dq_score_exception(from_report_id):
    """
    Given a DataQualityCounts object where one of the attributes is 0, throw
    a DQScoreException.
    """
    from_report_id.return_value = DataQualityCounts(
        lines=2, vehicle_journeys=120, data_set=1, timing_patterns=0, stops=40
    )
    report = DataQualityReportFactory()

    calculator = DataQualityCalculator(WEIGHTED_OBSERVATIONS)
    with pytest.raises(DQScoreException):
        calculator.calculate(report_id=report.id)


@pytest.mark.parametrize(
    "score,expected",
    [
        (1.0, DataQualityRAG(score=1.0, rag_level="green", css_indicator="success")),
        (0.91, DataQualityRAG(score=0.91, rag_level="amber", css_indicator="warning")),
        (0.9, DataQualityRAG(score=0.9, rag_level="red", css_indicator="error")),
        (0.89, DataQualityRAG(score=0.89, rag_level="red", css_indicator="error")),
    ],
)
def test_data_quality_rag(score, expected):
    actual = DataQualityRAG.from_score(score)
    assert actual == expected


@pytest.mark.parametrize(
    "score,expected",
    [
        (1.0, GREEN),
        (1.000000002, GREEN),
        (0.999, AMBER),
        (0.996, AMBER),
        (0.995, AMBER),
        (0.91, AMBER),
        (0.905, AMBER),
        (0.904, AMBER),
        (0.901, AMBER),
        (0.9005, RED),
        (0.9, RED),
        (0.895, RED),
        (0.89, RED),
    ],
)
def test_rag_boundaries(score, expected):
    rag = DataQualityRAG.from_score(score)
    assert rag.rag_level == expected
