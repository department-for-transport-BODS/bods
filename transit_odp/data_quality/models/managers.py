from django.db import models

from .querysets import (
    DataQualityReportQueryset,
    TimingMissingPointQueryset,
    TimingPatternStopQueryset,
    VehicleJourneyQueryset,
)


class TimingPatternStopManager(models.Manager.from_queryset(TimingPatternStopQueryset)):
    pass


class VehicleJourneyManager(models.Manager.from_queryset(VehicleJourneyQueryset)):
    pass


class DataQualityReportManager(models.Manager.from_queryset(DataQualityReportQueryset)):
    pass


class TimingMissingPointManager(
    models.Manager.from_queryset(TimingMissingPointQueryset)
):
    pass
