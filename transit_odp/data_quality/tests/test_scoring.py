from unittest.mock import patch
import pytest

from transit_odp.data_quality.etl import TransXChangeDQPipeline
from transit_odp.data_quality.factories.transmodel import (
    DataQualityReportFactory,
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
