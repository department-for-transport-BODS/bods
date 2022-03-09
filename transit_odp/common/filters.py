from django_filters import rest_framework as filters
from django_filters.constants import EMPTY_VALUES


class ArrayFilter(filters.CharFilter):
    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        return super().filter(qs, [value])
