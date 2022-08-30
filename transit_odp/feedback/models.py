from django.db import models
from django.utils import timezone

MAX_URL_LEN = 2048


class SatisfactionRating(models.IntegerChoices):
    VERY_SATISFIED = 1, "Very satisfied"
    SATISFIED = 2, "Satisfied"
    NEITHER_SATISFIED_NOR_DISSATISFIED = 3, "Neither satisfied nor dissatisfied"
    DISSATISFIED = 4, "Dissatisfied"
    VERY_DISSATISFIED = 5, "Very dissatisfied"


class Feedback(models.Model):
    date = models.DateField(default=timezone.localdate)
    page_url = models.CharField(max_length=MAX_URL_LEN)
    satisfaction_rating = models.IntegerField(choices=SatisfactionRating.choices)
    comment = models.CharField(max_length=1200, blank=True)
