from django import template
from django.conf import settings

register = template.Library()


# Template tag that checks if the feature flag is enabled based on the
# env var - IS_AVL_FEATURE_FLAG_ENABLED
@register.simple_tag
def is_avl_feature_flag_enabled() -> bool:
    return True if settings.IS_AVL_FEATURE_FLAG_ENABLED else False
