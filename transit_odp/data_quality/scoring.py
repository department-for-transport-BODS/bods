from dataclasses import dataclass
from typing import Dict, List, Optional

from pydantic import BaseModel

from transit_odp.common.utils import round_down
from transit_odp.data_quality.constants import (
    WEIGHTED_OBSERVATIONS,
    CheckBasis,
    Observation,
)
from transit_odp.data_quality.models.report import (
    DataQualityReport,
    DataQualityReportSummary,
)
from transit_odp.data_quality.models.transmodel import TimingPattern, VehicleJourney
from transit_odp.data_quality.models.warnings import DataQualityWarningBase
from transit_odp.organisation.models import DatasetRevision

INDICATOR_AMBER = "warning"
INDICATOR_GREEN = "success"
INDICATOR_RED = "error"

AMBER = "amber"
RED = "red"
GREEN = "green"

GREEN_THRESHOLD = 1.0
AMBER_THRESHOLD = 0.9


class DQScoreException(Exception):
    pass


@dataclass
class DataQualityRAG:
    score: float
    rag_level: str
    css_indicator: str

    @classmethod
    def from_score(cls, score: float):
        score = round_down(score)
        if score >= GREEN_THRESHOLD:
            return cls(score=score, rag_level=GREEN, css_indicator=INDICATOR_GREEN)
        elif score > AMBER_THRESHOLD:
            return cls(score=score, rag_level=AMBER, css_indicator=INDICATOR_AMBER)
        else:
            return cls(score=score, rag_level=RED, css_indicator=INDICATOR_RED)


@dataclass
class ScoreInput:
    model: DataQualityWarningBase
    weighting: float
    check_basis: str


class DataQualityCounts(BaseModel):
    data_set: int
    lines: int
    stops: int
    timing_patterns: int
    vehicle_journeys: int

    @classmethod
    def from_report_id(cls, report_id: int):
        revision = DatasetRevision.objects.get(report=report_id)
        lines = revision.num_of_lines or 1
        stops = revision.num_of_bus_stops or 1
        timing_patterns = (
            TimingPattern.objects.filter(service_pattern__service__reports=report_id)
            .order_by("id")
            .distinct()
        )
        vehicle_journeys = (
            VehicleJourney.objects.filter(
                timing_pattern__service_pattern__service__reports=report_id
            )
            .order_by("id")
            .distinct()
        )

        # data_set type warnings can have a maximum of 1 warning per data set.
        # we never want the count to be 0 so we us max(1, count)
        return cls(
            data_set=1,
            lines=max(1, lines),
            stops=max(1, stops),
            timing_patterns=max(1, timing_patterns.count()),
            vehicle_journeys=max(1, vehicle_journeys.count()),
        )


class DataQualityCalculator:
    def __init__(self, observations: Optional[List[Observation]] = None):
        """
        A class for calculating a Data Quality Score for a particular report.

        Args:
            observations: List[Observation] Observations to be used in the scoring.
        """

        self._inputs: Dict = {}
        self._counts: DataQualityCounts = None
        if observations is not None:
            for o in observations:
                self.register_observation(o)

    def register_observation(self, observation: Observation) -> None:
        """
        Register an observation to be used in the score calculation.
        """
        model_name = observation.model.__name__
        self._inputs[model_name] = ScoreInput(
            model=observation.model,
            weighting=observation.weighting,
            check_basis=observation.check_basis.value,
        )

    @property
    def inputs(self) -> List[ScoreInput]:
        return self._inputs.values()

    def get_counts(self, report_id: int) -> DataQualityCounts:
        """
        Get the counts for the "check basis" i.e. lines, stops, timing_patterns, etc
        """
        return DataQualityCounts.from_report_id(report_id=report_id)

    def calculate(self, report_id: int) -> float:
        """Calculates the total data quality score for a dataset revision."""
        counts = self.get_counts(report_id)
        total = 0
        summary = DataQualityReportSummary.objects.get(report_id=report_id)
        try:
            for input_ in self.inputs:
                observation_count = summary.data.get(input_.model.__name__, 0)
                if input_.check_basis == CheckBasis.data_set.value:
                    observation_count = int(observation_count > 0)

                check_basis_count = getattr(counts, input_.check_basis)
                weighting = input_.weighting
                total += (1.0 - observation_count / check_basis_count) * weighting
        except Exception as e:
            raise DQScoreException from e
        return round(total, 5)


def get_data_quality_rag(report: DataQualityReport):
    # Required for transition to saving dq score in the database
    if report.score > 0.0:
        return DataQualityRAG.from_score(report.score)

    calculator = DataQualityCalculator(WEIGHTED_OBSERVATIONS)
    try:
        score = calculator.calculate(report_id=report.id)
    except DQScoreException:
        rag = None
    else:
        report.score = score
        report.save()
        rag = DataQualityRAG.from_score(score)

    return rag
