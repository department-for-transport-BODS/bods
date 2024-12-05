from collections import defaultdict
from dataclasses import dataclass
from typing import List

from django.views.generic import TemplateView
from transit_odp.dqs.constants import (
    OBSERVATIONS,
    Level,
    Observation,
)
from waffle import flag_is_active


@dataclass
class GlossaryCategory:
    type: str
    observations: List[Observation]


def get_glossary_category_by_level(observations: List[Observation], level: Level):
    categories = defaultdict(list)
    for o in observations:
        if o.level is level:
            categories[o.type].append(o)
    return [GlossaryCategory(n, o) for n, o in categories.items()]


class DataQualityGlossaryView(TemplateView):
    template_name = "data_quality/definitions.html"

    @property
    def is_dqs_new_report(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        observations = OBSERVATIONS

        critical = get_glossary_category_by_level(observations, Level.critical)
        critical_count = sum(len(c.observations) for c in critical)

        advisory = get_glossary_category_by_level(observations, Level.advisory)
        advisory_count = sum(len(c.observations) for c in advisory)

        context.update(
            {
                "critical_observations": critical,
                "critical_count": critical_count,
                "advisory_count": advisory_count,
                "advisory_observations": advisory,
            }
        )
        return context


class DataQualityScoreGuidanceView(TemplateView):
    """
    A view for displaying the Data Quality Score guidance.
    """

    template_name = "data_quality/score_description.html"

    def get_context_data(self, **kwargs):
        # TODO: It will be removed in another BODS ticket
        context = super().get_context_data(**kwargs)
        observations = [o for o in OBSERVATIONS if o.weighting]
        observations = sorted(observations, key=lambda o: (-o.weighting, o.title))
        context.update({"observations": observations})
        return context
