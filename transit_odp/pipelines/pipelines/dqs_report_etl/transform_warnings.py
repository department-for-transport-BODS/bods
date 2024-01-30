import logging

import pandas as pd
from dateutil.parser import parse
from django.db.models import Q

from transit_odp.data_quality.models import (
    DataQualityReport,
    FastLinkWarning,
    JourneyConflictWarning,
    JourneyDateRangeBackwardsWarning,
    JourneyDuplicateWarning,
    JourneyStopInappropriateWarning,
    JourneyWithoutHeadsignWarning,
    ServicePattern,
    SlowLinkWarning,
    SlowTimingWarning,
    StopIncorrectTypeWarning,
    StopMissingNaptanWarning,
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
    transform_timing_warning(
        report, model, warnings.timing_fast_link, "timing_fast_link"
    )
    transform_timing_warning(
        report, model, warnings.timing_slow_link, "timing_slow_link"
    )
    transform_timing_warning(report, model, warnings.timing_slow, "timing_slow")

    transform_timing_backwards_warning(report, model, warnings.timing_backwards)
    transform_timing_pick_up_warning(report, model, warnings.timing_pick_up)
    transform_timing_drop_off_warning(report, model, warnings.timing_drop_off)

    transform_stop_missing_naptan_warning(report, model, warnings.stop_missing_naptan)
    transform_journey_stop_inappropriate_warning(
        report, model, warnings.journey_stop_inappropriate
    )

    transform_date_range_backwards_warning(
        report, model, warnings.journey_date_range_backwards
    )
    transform_journey_duplicate_warning(report, model, warnings.journey_duplicate)
    transform_journey_conflict_warning(report, model, warnings.journey_conflict)

    transform_journey_without_headsign_warning(
        report, model, warnings.journeys_without_headsign
    )

    transform_stop_incorrect_type_warning(report, model, warnings.stop_incorrect_type)


def transform_timing_warning(
    report: DataQualityReport,
    model: TransformedModel,
    warnings: pd.DataFrame,
    warning_type: str,
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

    warning_class_lookup = {
        "timing_fast_link": FastLinkWarning,
        "timing_slow_link": SlowLinkWarning,
        "timing_slow": SlowTimingWarning,
    }

    warning_class = warning_class_lookup[warning_type]

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

    # map the warning-type to the name of the rel on the through table back
    # to the warning class
    warning_class_rel_lookup = {
        "timing_fast_link": "fastlinkwarning_id",
        "timing_slow_link": "slowlinkwarning_id",
        "timing_slow": "slowtimingwarning_id",
    }
    warning_class_rel = warning_class_rel_lookup[warning_type]

    def create_stops_m2m():
        for warning in warnings[["id", "tps_ids"]].itertuples():
            for stop_id in list(warning.tps_ids):
                yield through_timings(
                    timingpatternstop_id=stop_id,
                    **{warning_class_rel: warning.id},
                )

    through_timings.objects.bulk_create(create_stops_m2m())

    # Create m2m with ServiceLink

    def get_service_links(service_links):
        if warning_type == "timing_fast_link" or warning_type == "timing_slow_link":
            service_links = [service_links]

        result = set(model.service_links.loc[list(set(service_links)), "id"])
        return list(result)

    if warning_type == "timing_fast_link" or warning_type == "timing_slow_link":
        related_service_links_field = "service_link"
    else:
        related_service_links_field = "entities"

    warnings["sl_ids"] = warnings[related_service_links_field].apply(
        lambda service_links: get_service_links(service_links)
    )

    through_sls = warning_class.service_links.through

    def create_service_link_m2m():
        for warning in warnings[["id", "sl_ids"]].itertuples():
            for sl_id in list(warning.sl_ids):
                yield through_sls(
                    servicelink_id=sl_id, **{warning_class_rel: warning.id}
                )

    through_sls.objects.bulk_create(create_service_link_m2m())


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


class StopMissingNaptanWarningLoader:
    def __init__(self, report_id, data):
        self.report_id = report_id
        self.data = data
        self._service_patterns = None

    def load(self, model):
        if len(self.data) == 0:
            return

        self.data = self.data.merge(
            model.stops["id"].rename("stop_id"),
            how="left",
            left_on="stop_ito_id",
            right_index=True,
        )

        self.create_warnings()

    @property
    def stop_ids(self):
        return self.data["stop_id"].tolist()

    @property
    def service_patterns(self):
        """Cache the service patterns so we only need to make one request per set
        of stop missing naptan warnings."""
        if self._service_patterns is not None:
            return self._service_patterns

        ito_ids = self.data.service_patterns.tolist()[0]
        self._service_patterns = list(ServicePattern.objects.filter(ito_id__in=ito_ids))
        return self._service_patterns

    def get_service_patterns(self, stop_id):
        """Filter the cached service patterns by stop id"""
        mask = self.data["stop_id"] == stop_id
        ito_ids = self.data[mask].iloc[0].service_patterns
        patterns = [sp for sp in self.service_patterns if sp.ito_id in ito_ids]
        return patterns

    def create_warnings(self):
        WarningClass = StopMissingNaptanWarning
        ThroughModel = StopMissingNaptanWarning.service_patterns.through

        warnings = [
            WarningClass(report_id=self.report_id, stop_id=stop_id)
            for stop_id in self.stop_ids
        ]
        warnings = WarningClass.objects.bulk_create(warnings)

        models = []
        for warning in warnings:
            patterns = self.get_service_patterns(warning.stop_id)
            for pattern in patterns:
                models.append(
                    ThroughModel(
                        servicepattern_id=pattern.id,
                        stopmissingnaptanwarning_id=warning.id,
                    )
                )
        ThroughModel.objects.bulk_create(models)


def transform_stop_missing_naptan_warning(
    report: DataQualityReport, model: TransformedModel, df: pd.DataFrame
):
    loader = StopMissingNaptanWarningLoader(report.id, df)
    loader.load(model)


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


def transform_journey_duplicate_warning(
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

    # Join duplicate vehicle_journey_id
    warnings = warnings.merge(
        model.vehicle_journeys[["id"]].rename(
            columns={"id": "duplicate_vehicle_journey_id"}
        ),
        how="left",
        left_on="duplicate",
        right_index=True,
    )

    warning_class = JourneyDuplicateWarning

    # Create warnings and associate with missing StopPoint
    def inner():
        for warning in warnings.itertuples():
            yield warning_class(
                report=report,
                vehicle_journey_id=warning.vehicle_journey_id,
                duplicate=VehicleJourney.objects.get(
                    id=warning.duplicate_vehicle_journey_id
                ),
            )

    warning_class.objects.bulk_create(inner())


def transform_journey_conflict_warning(
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

    # Join conflict vehicle_journey_id
    warnings = warnings.merge(
        model.vehicle_journeys[["id"]].rename(
            columns={"id": "conflict_vehicle_journey_id"}
        ),
        how="left",
        left_on="conflict",
        right_index=True,
    )

    warning_class = JourneyConflictWarning

    # Create warnings and associate with missing StopPoint
    def inner():
        for warning in warnings.itertuples():
            obj = warning_class(
                report=report,
                vehicle_journey_id=warning.vehicle_journey_id,
                conflict=VehicleJourney.objects.get(
                    id=warning.conflict_vehicle_journey_id
                ),
            )

            stops = StopPoint.objects.filter(ito_id__in=warning.stops)
            obj.stops.set(stops),
            yield obj

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


def transform_stop_incorrect_type_warning(
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

    warning_class = StopIncorrectTypeWarning

    # Create warnings and associate with missing StopPoint
    def inner():
        for warning in warnings.itertuples():
            obj = warning_class(
                report=report,
                stop_id=warning.stop_id,
                stop=StopPoint.objects.get(ito_id=warning.stop_ito_id),
                stop_type=warning.stop_type,
            )

            service_patterns = ServicePattern.objects.filter(
                ito_id__in=warning.service_patterns
            )

            obj.service_patterns.set(service_patterns)
            yield obj

    warning_class.objects.bulk_create(inner())
