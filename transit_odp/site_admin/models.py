from django.contrib.auth import get_user_model
from django.db import models
from django_extensions.db.models import TimeStampedModel

from transit_odp.common.utils.repr import nice_repr

User = get_user_model()
CHAR_LEN = 512


class OperationalStats(models.Model):
    date = models.DateField(unique=True)

    #  operator and user counts
    operator_count = models.IntegerField()
    operator_user_count = models.IntegerField()
    agent_user_count = models.IntegerField()
    consumer_count = models.IntegerField()

    # active dataset counts
    timetables_count = models.IntegerField()
    avl_count = models.IntegerField()
    fares_count = models.IntegerField()

    # number of operators with at least one published dataset
    published_timetable_operator_count = models.IntegerField()
    published_avl_operator_count = models.IntegerField()
    published_fares_operator_count = models.IntegerField()

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id!r}, date={self.date!s})"

    class Meta:
        verbose_name_plural = "Operational stats"


class APIRequest(TimeStampedModel):
    requestor = models.ForeignKey(User, on_delete=models.CASCADE)
    path_info = models.CharField(max_length=CHAR_LEN)
    query_string = models.CharField(max_length=CHAR_LEN)

    def __str__(self):
        return nice_repr(self)
