import logging

import pandas as pd
from dateutil.parser import parse
from django.db.models import Q

from transit_odp.data_quality.models import (
    DataQualityReport,
    JourneyDateRangeBackwardsWarning,
    JourneyStopInappropriateWarning,
    JourneyWithoutHeadsignWarning,
    ServicePattern,
    StopPoint,
    TimingBackwardsWarning,
    TimingDropOffWarning,
    TimingPatternStop,
    TimingPickUpWarning,
    VehicleJourney,
)
from transit_odp.pipelines.pipelines.dqs_report_etl.models import (
    ExtractedWarnings,
    TransformedModel,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 100000


def run(
    report: DataQualityReport, model: TransformedModel, warnings: ExtractedWarnings
):

    transform_timing_backwards_warning(report, model, warnings.timing_backwards)
    transform_timing_pick_up_warning(report, model, warnings.timing_pick_up)
    transform_timing_drop_off_warning(report, model, warnings.timing_drop_off)

    transform_journey_stop_inappropriate_warning(
        report, model, warnings.journey_stop_inappropriate
    )

    transform_date_range_backwards_warning(
        report, model, warnings.journey_date_range_backwards
    )

    transform_journey_without_headsign_warning(
        report, model, warnings.journeys_without_headsign
    )


def transform_timing_backwards_warning(
    report: DataQualityReport, model: TransformedModel, warnings: pd.DataFrame
):
    if len(warnings) == 0:
        return

    # Join timing_pattern_id and service_pattern_id
    warnings = warnings.merge(
        model.timing_patterns[["id", "service_pattern_id"]].rename(
            columns={"id": "timing_pattern_id"}
        ),
        how="left",
        left_on="timing_pattern_ito_id",
        right_index=True,
    )

    warning_class = TimingBackwardsWarning

    # Load warnings
    def inner():
        for warning in warnings.itertuples():

            service_link_index = warning.indexes[0]

            from_stop = TimingPatternStop.objects.add_position().get(
                Q(timing_pattern_id=warning.timing_pattern_id)
                & Q(position=service_link_index)
            )

            to_stop = TimingPatternStop.objects.add_position().get(
                Q(timing_pattern_id=warning.timing_pattern_id)
                & Q(position=service_link_index + 1)
            )

            yield warning_class(
                report=report,
                timing_pattern_id=warning.timing_pattern_id,
                from_stop=from_stop,
                to_stop=to_stop,
            )

    warning_class.objects.bulk_create(inner())


def transform_timing_drop_off_warning(
    report: DataQualityReport, model: TransformedModel, warnings: pd.DataFrame
):
    if len(warnings) == 0:
        return

    # Join timing_pattern_id and service_pattern_id
    warnings = warnings.merge(
        model.timing_patterns[["id", "service_pattern_id"]].rename(
            columns={"id": "timing_pattern_id"}
        ),
        how="left",
        left_on="timing_pattern_ito_id",
        right_index=True,
    )

    warning_class = TimingDropOffWarning

    # Load warnings
    def inner():
        for record in warnings.itertuples():
            yield warning_class(
                report=report, timing_pattern_id=record.timing_pattern_id
            )

    warnings_objs = warning_class.objects.bulk_create(inner())

    # Create m2m of associated stops and service links

    # Join internal ids onto DataFrame
    warnings["id"] = [w.id for w in warnings_objs]

    # Convert 'indexes' list into TPSs
    warnings["tps_ids"] = warnings[["timing_pattern_id", "indexes"]].apply(
        lambda x: set(
            model.timing_pattern_stops.loc[
                [(x["timing_pattern_id"], indx) for indx in x["indexes"]],
                "timing_pattern_stop_id",
            ]
        ),
        axis=1,
    )

    through_timings = warning_class.timings.through

    warning_class_rel = "timingdropoffwarning_id"

    def create_stops_m2m():
        for warning in warnings[["id", "tps_ids"]].itertuples():
            for stop_id in list(warning.tps_ids):
                yield through_timings(
                    timingpatternstop_id=stop_id,
                    **{warning_class_rel: warning.id},
                )

    through_timings.objects.bulk_create(create_stops_m2m())


def transform_timing_pick_up_warning(
    report: DataQualityReport, model: TransformedModel, warnings: pd.DataFrame
):
    if len(warnings) == 0:
        return

    # Join timing_pattern_id and service_pattern_id
    warnings = warnings.merge(
        model.timing_patterns[["id", "service_pattern_id"]].rename(
            columns={"id": "timing_pattern_id"}
        ),
        how="left",
        left_on="timing_pattern_ito_id",
        right_index=True,
    )

    warning_class = TimingPickUpWarning

    # Load warnings
    def inner():
        for record in warnings.itertuples():
            yield warning_class(
                report=report, timing_pattern_id=record.timing_pattern_id
            )

    warnings_objs = warning_class.objects.bulk_create(inner())

    # Create m2m of associated stops and service links

    # Join internal ids onto DataFrame
    warnings["id"] = [w.id for w in warnings_objs]

    # Convert 'indexes' list into TPSs
    warnings["tps_ids"] = warnings[["timing_pattern_id", "indexes"]].apply(
        lambda x: set(
            model.timing_pattern_stops.loc[
                [(x["timing_pattern_id"], indx) for indx in x["indexes"]],
                "timing_pattern_stop_id",
            ]
        ),
        axis=1,
    )

    through_timings = warning_class.timings.through

    warning_class_rel = "timingpickupwarning_id"

    def create_stops_m2m():
        for warning in warnings[["id", "tps_ids"]].itertuples():
            for stop_id in list(warning.tps_ids):
                yield through_timings(
                    timingpatternstop_id=stop_id,
                    **{warning_class_rel: warning.id},
                )

    through_timings.objects.bulk_create(create_stops_m2m())


def transform_journey_stop_inappropriate_warning(
    report: DataQualityReport, model: TransformedModel, warnings: pd.DataFrame
):
    if len(warnings) == 0:
        return

    # Join stop_id
    warnings = warnings.merge(
        model.stops["id"].rename("stop_id"),
        how="left",
        left_on="stop_ito_id",
        right_index=True,
    )

    warning_class = JourneyStopInappropriateWarning

    # Create warnings and associate with missing StopPoint
    def inner():
        for warning in warnings.itertuples():
            if warning.stop_type == "BCT":
                continue
            obj = warning_class(
                report=report,
                stop_id=warning.stop_id,
                stop=StopPoint.objects.get(ito_id=warning.stop_ito_id),
                stop_type=warning.stop_type,
            )

            vehicle_journeys = VehicleJourney.objects.filter(
                ito_id__in=warning.vehicle_journeys
            )

            obj.vehicle_journeys.set(vehicle_journeys)
            yield obj

    warning_class.objects.bulk_create(inner())


def transform_date_range_backwards_warning(
    report: DataQualityReport, model: TransformedModel, warnings: pd.DataFrame
):
    if len(warnings) == 0:
        return

    # Join vehicle_journey_id
    warnings = warnings.merge(
        model.vehicle_journeys[["id"]].rename(columns={"id": "vehicle_journey_id"}),
        how="left",
        left_on="vehicle_journey_ito_id",
        right_index=True,
    )

    warning_class = JourneyDateRangeBackwardsWarning

    # Create warnings and associate with missing StopPoint
    def inner():
        for warning in warnings.itertuples():
            yield warning_class(
                report=report,
                vehicle_journey_id=warning.vehicle_journey_id,
                start=parse(warning.start),
                end=parse(warning.end),
            )

    warning_class.objects.bulk_create(inner())


def transform_journey_without_headsign_warning(
    report: DataQualityReport, model: TransformedModel, warnings: pd.DataFrame
):
    if len(warnings) == 0:
        return

    # Join vehicle_journey_id
    warnings = warnings.merge(
        model.vehicle_journeys[["id"]].rename(columns={"id": "vehicle_journey_id"}),
        how="left",
        left_on="vehicle_journey_ito_id",
        right_index=True,
    )

    warning_class = JourneyWithoutHeadsignWarning

    # Create warnings and associate with missing StopPoint
    def inner():
        for warning in warnings.itertuples():
            yield warning_class(
                report=report,
                vehicle_journey_id=warning.vehicle_journey_id,
            )

    warning_class.objects.bulk_create(inner())
