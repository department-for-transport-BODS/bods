from django.db import models
from django.db.models import F

from transit_odp.common.querysets import GroupConcat


class ServicePatternStopQuerySet(models.QuerySet):
    def add_location(self):
        return self.annotate(location=F("naptan_stop__location"))


class ServicePatternQuerySet(models.QuerySet):
    def add_service_name(self):
        # TODO - the data model isn't quite right here, a ServicePattern should
        # relate to a single Service.
        # There should be another table 'Route' which defines the geographic entity,
        # stop sequence, etc. The data model would be Service m2m Route through
        # ServicePattern. This would allow the ServicePattern to has service specific
        # data, such as as the service name
        return self.annotate(service_name=GroupConcat("services__name", ", "))
