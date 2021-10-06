from django.db import models

from transit_odp.changelog.constants import ConsumerIssue, PublisherIssue


class ConsumerKnownIssueManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(category=ConsumerIssue)

    def create(self, **kwargs):
        kwargs.update({"category": ConsumerIssue})
        return super().create(**kwargs)


class PublisherKnownIssueManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(category=PublisherIssue)

    def create(self, **kwargs):
        kwargs.update({"category": PublisherIssue})
        return super().create(**kwargs)
