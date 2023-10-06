import logging
from django import template

from transit_odp.disruptions.models import DisruptionReasonsEnum

logger = logging.getLogger(__name__)

register = template.Library()


@register.filter
def top_three_reasons(dictionary):
    # Sort the dictionary by values in descending order and take the top three items
    top_reasons = []
    count = 0
    if dictionary is not None and isinstance(dictionary, dict):
        sorted_items = sorted(dictionary.items(), key=lambda x: x[1], reverse=True)
        for item in sorted_items:
            if count == 3:
                break
            key = item[0]
            try:
                enum_value = dict(DisruptionReasonsEnum.choices)[key]
                top_reasons.append(enum_value)
                count += 1
            except KeyError:
                logger.error(
                    f"KeyError: Key '{key}' not found in DisruptionReasonsEnum.choices"
                )
                continue

    return top_reasons
