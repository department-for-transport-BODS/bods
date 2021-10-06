from unittest.mock import patch

import pytest

from transit_odp.data_quality.constants import (
    WEIGHTED_OBSERVATIONS,
    BackwardDateRangeObservation,
    BackwardsTimingObservation,
    CheckBasis,
    FastTimingPointObservation,
    FirstStopSetDownOnlyObservation,
    IncorrectNocObservation,
    IncorrectStopTypeObservation,
    LastStopPickUpOnlyObservation,
    MissingBlockNumber,
    StopNotInNaptanObservation,
)
from transit_odp.data_quality.etl import TransXChangeDQPipeline
from transit_odp.data_quality.factories.transmodel import (
    DataQualityReportFactory,
    ServicePatternStopFactory,
)
from transit_odp.data_quality.factories.warnings import (
    FastTimingWarningFactory,
    IncorrectNOCWarningFactory,
    JourneyDateRangeBackwardsWarningFactory,
    JourneyStopInappropriateWarningFactory,
    LineMissingBlockIDWarningFactory,
    StopMissingNaptanWarningFactory,
    TimingBackwardsWarningFactory,
    TimingDropOffWarningFactory,
    TimingPickUpWarningFactory,
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
def test_score_calculation_with_stops_component(from_report_id):
    """
    Given that the data quality report contains various `stop` related warnings
    calculate the data quality score correctly.

    Possible warnings:
        JourneyStopInappropriateWarning
        StopMissingNaptanWarning
    """
    stops_count = DQ_COUNTS.stops
    report = DataQualityReportFactory()
    expected_score = sum(
        o.weighting
        for o in WEIGHTED_OBSERVATIONS
        if not o.check_basis == CheckBasis.stops
    )

    sps = ServicePatternStopFactory()

    missing_count = 3
    missing_weight = StopNotInNaptanObservation.weighting
    StopMissingNaptanWarningFactory.create_batch(
        missing_count, stop=sps.stop, report=report
    )
    missing_score = score_contribution(missing_count, stops_count, missing_weight)

    # add in warning where stop has no service pattern
    # this should have no impact on the score
    StopMissingNaptanWarningFactory(report=report)

    incorrect_count = 2
    incorrect_weight = IncorrectStopTypeObservation.weighting
    JourneyStopInappropriateWarningFactory.create_batch(
        incorrect_count, report=report, stop=sps.stop
    )
    incorrect_score = score_contribution(incorrect_count, stops_count, incorrect_weight)

    expected_score += missing_score + incorrect_score

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

    block_count = 4
    block_weight = MissingBlockNumber.weighting
    LineMissingBlockIDWarningFactory.create_batch(block_count, report=report)
    block_score = score_contribution(block_count, line_count, block_weight)

    expected_score += block_score

    pipeline = TransXChangeDQPipeline(report)
    pipeline.load_summary()
    calculator = DataQualityCalculator(WEIGHTED_OBSERVATIONS)
    score = calculator.calculate(report.id)
    assert pytest.approx(score, SCORE_TOLERANCE) == expected_score


@patch(DQC_FROM_REPORT_ID, return_value=DQ_COUNTS)
def test_score_calculation_timing_patterns_component(from_report_id):
    """
    Test that the score is calculated correctly with one or more observations
    that are concerned with the `timing_patterns` feature.

    Possible warnings:
        FastTimingWarning
        TimingBackwardsWarning
        TimingDropOffWarning
        TimingPickUpWarning
    """
    report = DataQualityReportFactory()
    timing_patterns = DQ_COUNTS.timing_patterns
    expected_score = sum(
        o.weighting
        for o in WEIGHTED_OBSERVATIONS
        if not o.check_basis == CheckBasis.timing_patterns
    )

    fast_timing_count = 6
    fast_timing_weight = FastTimingPointObservation.weighting
    FastTimingWarningFactory.create_batch(fast_timing_count, report=report)
    fast_timing_score = score_contribution(
        fast_timing_count, timing_patterns, fast_timing_weight
    )

    pickup_count = 1
    pickup_weight = LastStopPickUpOnlyObservation.weighting
    TimingPickUpWarningFactory.create_batch(pickup_count, report=report)
    pickup_score = score_contribution(pickup_count, timing_patterns, pickup_weight)

    dropoff_count = 0
    dropoff_weight = FirstStopSetDownOnlyObservation.weighting
    TimingDropOffWarningFactory.create_batch(dropoff_count, report=report)
    dropoff_score = score_contribution(dropoff_count, timing_patterns, dropoff_weight)

    backwards_count = 0
    backwards_weight = BackwardsTimingObservation.weighting
    TimingBackwardsWarningFactory.create_batch(backwards_count, report=report)
    backwards_score = score_contribution(
        backwards_count, timing_patterns, backwards_weight
    )

    expected_score += fast_timing_score + dropoff_score + pickup_score + backwards_score
    pipeline = TransXChangeDQPipeline(report)
    pipeline.load_summary()
    calculator = DataQualityCalculator(WEIGHTED_OBSERVATIONS)
    score = calculator.calculate(report.id)
    assert pytest.approx(score, SCORE_TOLERANCE) == expected_score


@patch(DQC_FROM_REPORT_ID, return_value=DQ_COUNTS)
def test_score_calculation_vehicle_journeys_component(from_report_id):
    """
    Test that the score is calculated correctly with one or more observations
    that are concerned with the `timing_patterns` feature.

    Possible warnings:
        JourneyWithoutHeadsignWarning
        JourneyDateRangeBackwardsWarning
    """
    report = DataQualityReportFactory()
    vehicle_journeys = DQ_COUNTS.vehicle_journeys
    expected_score = sum(
        o.weighting
        for o in WEIGHTED_OBSERVATIONS
        if not o.check_basis == CheckBasis.vehicle_journeys
    )

    backwards_count = 4
    backwards_weight = BackwardDateRangeObservation.weighting
    JourneyDateRangeBackwardsWarningFactory.create_batch(backwards_count, report=report)
    backwards_score = score_contribution(
        backwards_count, vehicle_journeys, backwards_weight
    )

    expected_score += backwards_score

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
        (0.996, AMBER),
        (0.995, AMBER),
        (0.91, AMBER),
        (0.905, RED),
        (0.904, RED),
        (0.901, RED),
        (0.9, RED),
        (0.895, RED),
        (0.89, RED),
    ],
)
def test_rag_boundaries(score, expected):
    rag = DataQualityRAG.from_score(score)
    assert rag.rag_level == expected
