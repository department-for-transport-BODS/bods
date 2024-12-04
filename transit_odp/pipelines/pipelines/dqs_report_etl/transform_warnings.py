import logging

import pandas as pd
from dateutil.parser import parse
from django.db.models import Q

from transit_odp.data_quality.models import (
    DataQualityReport,
    ServicePattern,
    StopPoint,
    TimingPatternStop,
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

    transform_timing_pick_up_warning(report, model, warnings.timing_pick_up)


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
