from collections import defaultdict
from dataclasses import dataclass
from typing import List

from django.views.generic import TemplateView

from transit_odp.data_quality.constants import OBSERVATIONS
from transit_odp.dqs.constants import (
    OBSERVATIONS as DQSOBSERVATIONS,
    Level,
    Observation,
    FEEDBACK_INTRO,
)
from waffle import flag_is_active


@dataclass
class GlossaryCategory:
    type: str
    observations: List[Observation]
    show_category_type: bool = True


def get_glossary_category_by_level(
    observations: List[Observation], level: Level, show_category: bool = True
):
    categories = defaultdict(list)
    for o in observations:
        if o.level is level:
            categories[o.type].append(o)
    return [GlossaryCategory(n, o, show_category) for n, o in categories.items()]


class DataQualityGlossaryView(TemplateView):
    template_name = "data_quality/definitions.html"

    @property
    def is_dqs_new_report(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        observations = OBSERVATIONS
        if self.is_dqs_new_report:
            observations = DQSOBSERVATIONS

        critical = get_glossary_category_by_level(observations, Level.critical)
        critical_count = sum(len(c.observations) for c in critical)

        advisory = get_glossary_category_by_level(observations, Level.advisory)
        advisory_count = sum(len(c.observations) for c in advisory)

        feedback = get_glossary_category_by_level(
            observations, Level.feedback, show_category=False
        )

        context.update(
            {
                "critical_count": critical_count,
                "critical_observations": critical,
                "advisory_count": advisory_count,
                "advisory_observations": advisory,
                "feedback_count": 1,
                "feedback_observations": feedback,
                "feedback_intro": FEEDBACK_INTRO,
                "is_specific_feedback": flag_is_active("", "is_specific_feedback"),
            }
        )
        return context


class DataQualityScoreGuidanceView(TemplateView):
    """
    A view for displaying the Data Quality Score guidance.
    """

    template_name = "data_quality/score_description.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        observations = [o for o in OBSERVATIONS if o.weighting]
        observations = sorted(observations, key=lambda o: (-o.weighting, o.title))
        context.update({"observations": observations})
        return context
