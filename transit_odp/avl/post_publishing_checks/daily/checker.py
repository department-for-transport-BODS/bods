import datetime
import logging
from typing import List
from ddtrace import tracer

from transit_odp.avl.post_publishing_checks.constants import MiscFieldPPC, SirivmField
from transit_odp.avl.post_publishing_checks.daily.data_matching import DataMatching
from transit_odp.avl.post_publishing_checks.daily.results import ValidationResult
from transit_odp.avl.post_publishing_checks.daily.sirivm_sampler import (
    SiriHeader,
    SirivmSampler,
)
from transit_odp.avl.post_publishing_checks.daily.vehicle_journey_finder import (
    VehicleJourneyFinder,
)
from transit_odp.avl.post_publishing_checks.daily.writer import (
    PostPublishingResultsJsonWriter,
)
from transit_odp.avl.post_publishing_checks.models import VehicleActivity
from transit_odp.organisation.models import Dataset

logger = logging.getLogger(__name__)


class PostPublishingChecker:
    def get_avl_feed_name(self, data_feed_id: int) -> str:
        data_feed = Dataset.objects.filter(id=data_feed_id).select_related(
            "live_revision"
        )
        return "" if data_feed.count() == 0 else data_feed.first().live_revision.name

    def record_vehicle_activity(
        self,
        feed_id: int,
        sirivm_header: SiriHeader,
        activity: VehicleActivity,
        result: ValidationResult,
    ):
        mvj = activity.monitored_vehicle_journey
        logger.info(f"Operator ref: {mvj.operator_ref}")
        logger.info(f"Line ref: {mvj.line_ref}")
        if mvj.framed_vehicle_journey_ref is None:
            logger.info("Dated vehicle journey ref: None")
        else:
            logger.info(
                "Dated vehicle journey ref: "
                f"{mvj.framed_vehicle_journey_ref.dated_vehicle_journey_ref}"
            )

        for key, value in sirivm_header.items():
            result.set_sirivm_value(key, value)

        result.set_misc_value(MiscFieldPPC.BODS_DATA_FEED_ID, feed_id)
        result.set_misc_value(
            MiscFieldPPC.BODS_DATA_FEED_NAME, self.get_avl_feed_name(feed_id)
        )

        result.set_sirivm_value(SirivmField.RECORDED_AT_TIME, activity.recorded_at_time)
        result.set_sirivm_value(SirivmField.ITEM_IDENTIFIER, activity.item_identifier)
        result.set_sirivm_value(SirivmField.VALID_UNTIL_TIME, activity.valid_until_time)
        result.set_sirivm_value(SirivmField.OPERATOR_REF, mvj.operator_ref)
        result.set_sirivm_value(SirivmField.LINE_REF, mvj.line_ref)
        result.set_sirivm_value(SirivmField.ORIGIN_NAME, mvj.origin_name)
        result.set_sirivm_value(
            SirivmField.ORIGIN_AIMED_DEPARTURE_TIME,
            mvj.origin_aimed_departure_time,
        )
        result.set_sirivm_value(
            SirivmField.DIRECTION_REF,
            mvj.direction_ref,
            mvj.direction_ref_linenum,
        )
        result.set_sirivm_value(
            SirivmField.BLOCK_REF, mvj.block_ref, mvj.block_ref_linenum
        )
        result.set_sirivm_value(
            SirivmField.PUBLISHED_LINE_NAME, mvj.published_line_name
        )
        result.set_sirivm_value(
            SirivmField.DESTINATION_REF,
            mvj.destination_ref,
            mvj.destination_ref_linenum,
        )
        result.set_sirivm_value(
            SirivmField.ORIGIN_REF, mvj.origin_ref, mvj.origin_ref_linenum
        )
        result.set_sirivm_value(SirivmField.DESTINATION_NAME, mvj.destination_name)
        result.set_sirivm_value(SirivmField.BEARING, mvj.bearing)
        result.set_sirivm_value(SirivmField.VEHICLE_REF, mvj.vehicle_ref)
        if mvj.vehicle_location is not None:
            result.set_sirivm_value(
                SirivmField.LONGITUDE, mvj.vehicle_location.longitude
            )
            result.set_sirivm_value(SirivmField.LATITUDE, mvj.vehicle_location.latitude)
        if mvj.extensions is not None and mvj.extensions.vehicle_journey is not None:
            result.set_sirivm_value(
                SirivmField.DRIVER_REF,
                mvj.extensions.vehicle_journey.driver_ref,
            )
        if mvj.framed_vehicle_journey_ref is not None:
            result.set_sirivm_value(
                SirivmField.DATA_FRAME_REF,
                mvj.framed_vehicle_journey_ref.data_frame_ref,
            )
            result.set_sirivm_value(
                SirivmField.DATED_VEHICLE_JOURNEY_REF,
                mvj.framed_vehicle_journey_ref.dated_vehicle_journey_ref,
            )
        return result

    @tracer.wrap(
        service="task_daily_post_publishing_checks_single_feed",
        resource="perform_checks",
    )
    def perform_checks(
        self,
        activity_date: datetime.date,
        feed_id: int,
        num_activities: int = 20,
    ):
        sampler = SirivmSampler()
        sirivm_header, activities = sampler.get_vehicle_activities(
            feed_id,
            num_activities,
        )

        if len(activities) == 0:
            logger.info(f"Feed ID {feed_id}: No vehicle activity to validate")

        vehicle_journey_finder = VehicleJourneyFinder()
        data_matching = DataMatching()
        results: List[ValidationResult] = []

        for idx, activity in enumerate(activities):
            logger.info(f"FEED ID {feed_id} VEHICLE ACTIVITY #{idx}")
            result = ValidationResult()
            self.record_vehicle_activity(feed_id, sirivm_header, activity, result)

            txc_vehicle_journey = (
                vehicle_journey_finder.match_vehicle_activity_to_vehicle_journey(
                    activity, result
                )
            )

            if txc_vehicle_journey:
                data_matching.data_match(activity, txc_vehicle_journey, result)

            if result:
                results.append(result)

        results_writer = PostPublishingResultsJsonWriter(activity_date, feed_id)
        results_writer.write_results(results)
