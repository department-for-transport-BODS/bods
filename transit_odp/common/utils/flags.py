from dataclasses import dataclass

from django.conf import settings


@dataclass
class Feature:
    avl: bool = settings.IS_AVL_FEATURE_FLAG_ENABLED
    fares: bool = settings.IS_FARES_FEATURE_FLAG_ENABLED
