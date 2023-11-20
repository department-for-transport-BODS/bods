import logging
from django import template

from transit_odp.disruptions.models import DisruptionReasonsEnum


register = template.Library()


@register.filter
def top_three_reasons(dictionary):
    # Sort the dictionary by values in descending order and take the top three items
    if dictionary is not None and isinstance(dictionary, dict):
        return [
            dict(DisruptionReasonsEnum.choices)[k]
            for k, _ in sorted(
                dictionary.items(), key=lambda item: item[1], reverse=True
            )
            if k in dict(DisruptionReasonsEnum.choices)
        ][0:3]
