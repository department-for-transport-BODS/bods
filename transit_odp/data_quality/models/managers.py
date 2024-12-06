from django.db import models

from .querysets import (
    DataQualityReportQueryset,
    TimingPatternStopQueryset,
    VehicleJourneyQueryset,
)


class TimingPatternStopManager(models.Manager.from_queryset(TimingPatternStopQueryset)):
    pass


class VehicleJourneyManager(models.Manager.from_queryset(VehicleJourneyQueryset)):
    pass


class DataQualityReportManager(models.Manager.from_queryset(DataQualityReportQueryset)):
    pass
