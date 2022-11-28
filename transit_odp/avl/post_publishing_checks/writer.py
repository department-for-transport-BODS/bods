import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List

from django.core.files.base import ContentFile

from transit_odp.avl.models import PostPublishingCheckReport, PPCReportType
from transit_odp.avl.proxies import AVLDataset
from transit_odp.common.constants import UTF8

from .constants import SIRIVM_TO_TXC_MAP, ErrorCategory, MiscFieldPPC, SirivmField
from .results import ValidationResult


class FieldStat:
    def __init__(self, sirivm_field: SirivmField):
        self.sirivm_field = sirivm_field
        self.count_present = 0
        self.count_matches = 0


class PostPublishingResultsJsonWriter:
    def __init__(self, feed_id: int, logger: logging.Logger):
        self.feed_id = feed_id
        self.logger = logger
        self.json_report = {}
        self.complete_matches = 0

    def pretty_print(self, field: Any) -> str:
        if field is None:
            return "-"
        if field is True:
            return "Yes"
        if field is False:
            return "No"
        if isinstance(field, date) or isinstance(field, datetime):
            return field.isoformat()
        return str(field)

    def write_results(self, results: List[ValidationResult]):
        self.compile_results(results)
        today = date.today()
        filename = f"Day {today:%02d_%02m_%y}_feed_{self.feed_id}.json"
        content_file = ContentFile(
            json.dumps(self.json_report).encode(UTF8), name=filename
        )
        total_analysed = len(results)

        # data_feed = Dataset.objects.get(id=self.feed_id)
        # For debugging, need to save the PPC report against a real AVL feed, rather
        # than the one on production this task was run with.
        data_feed = AVLDataset.objects.first()

        ppc_report, created = PostPublishingCheckReport.objects.get_or_create(
            dataset=data_feed,
            created=today,
            granularity=PPCReportType.DAILY,
        )
        if created:
            ppc_report.file = content_file
            ppc_report.vehicle_activities_analysed = total_analysed
            ppc_report.vehicle_activities_completely_matching = self.complete_matches
            ppc_report.save()
        else:
            self.logger.warning(
                "PPC report not created: One already exists for feed id "
                f"{self.feed_id} on {today}"
            )

    def compile_results(self, results: List[ValidationResult]):
        self.json_report[
            "AVLtoTimetable matching summary"
        ] = self.compile_ppc_summary_report(results)
        self.json_report["All SIRI-VM analysed"] = self.compile_siri_message_analysed(
            results
        )
        self.json_report[
            "UncountedVehicleActivities"
        ] = self.compile_uncounted_vehicle_activities(results)
        self.json_report["DirectionRef"] = self.compile_direction_ref(results)
        self.json_report["DestinationRef"] = self.compile_destination_ref(results)
        self.json_report["OriginRef"] = self.compile_origin_ref(results)
        self.json_report["BlockRef"] = self.compile_block_ref(results)

    def compile_ppc_summary_report(self, results: List[ValidationResult]) -> List[Dict]:
        field_stats = [FieldStat(field) for field in SIRIVM_TO_TXC_MAP.keys()]
        num_mandatory_fields = len(
            [
                field
                for field in SIRIVM_TO_TXC_MAP.keys()
                if field != SirivmField.BLOCK_REF
            ]
        )
        for result in results:
            num_matching_fields = 0
            for field in field_stats:
                if result.sirivm_value(field.sirivm_field) is not None:
                    field.count_present += 1
                    if result.matches(field.sirivm_field):
                        field.count_matches += 1
                        if field != SirivmField.BLOCK_REF:
                            num_matching_fields += 1
            if num_matching_fields == num_mandatory_fields:
                self.complete_matches += 1
        ppc_summary_report_json = []

        block_ref_notes = (
            "Enforcement agency may consider this data as a mandatory field if you "
            "are technologically enabled to generate it. Please work with your "
            "suppliers to ensure it is provided accurately"
        )
        for field in field_stats:
            field_json = {
                "SIRI field": field.sirivm_field.value,
                "TXC match field": SIRIVM_TO_TXC_MAP[field.sirivm_field],
                "Total vehicleActivities analysed": len(results),
                "Total count of SIRI fields populated": field.count_present,
                "%populated": str(round(field.count_present * 100 / len(results), 1))
                + "%",
                "Successful match with TXC": str(field.count_matches),
                "%match": str(round(field.count_matches * 100 / len(results), 1)) + "%",
                "Notes": block_ref_notes
                if field.sirivm_field == SirivmField.BLOCK_REF
                else "",
            }
            ppc_summary_report_json.append(field_json)
        return ppc_summary_report_json

    def compile_siri_message_analysed(
        self, results: List[ValidationResult]
    ) -> List[Dict]:
        siri_message_analysed_json = []
        for result in results:
            vehicle_activity = {
                field.value: self.pretty_print(result.sirivm_value(field))
                for field in SirivmField
            }
            siri_message_analysed_json.append(vehicle_activity)
        return siri_message_analysed_json

    def compile_uncounted_vehicle_activities(
        self, results: List[ValidationResult]
    ) -> List[Dict]:
        uncounted_vehicle_activities_json = []
        for result in results:
            if result.txc_value(
                SirivmField.DATED_VEHICLE_JOURNEY_REF
            ) != result.sirivm_value(SirivmField.DATED_VEHICLE_JOURNEY_REF):
                vehicle_activity = {
                    "SD ResponseTimestamp": result.sirivm_value(
                        SirivmField.RESPONSE_TIMESTAMP_SD
                    ),
                    "AVL data set name BODS": result.misc_value(
                        MiscFieldPPC.BODS_DATA_FEED_NAME
                    ),
                    "AVL data set ID BODS": result.misc_value(
                        MiscFieldPPC.BODS_DATA_FEED_ID
                    ),
                    "OperatorRef": result.sirivm_value(SirivmField.OPERATOR_REF),
                    "LineRef": result.sirivm_value(SirivmField.LINE_REF),
                    "RecordedAtTime": result.sirivm_value(SirivmField.RECORDED_AT_TIME),
                    "DatedVehicleJourneyRef in SIRI": result.sirivm_value(
                        SirivmField.DATED_VEHICLE_JOURNEY_REF
                    ),
                    "Error note: Reason it could not be analysed against "
                    "TXC": "\n".join(result.errors.get(ErrorCategory.GENERAL)),
                }
                vehicle_activity = {
                    k: self.pretty_print(v) for k, v in vehicle_activity.items()
                }
                uncounted_vehicle_activities_json.append(vehicle_activity)
        return uncounted_vehicle_activities_json

    def compile_direction_ref(self, results: List[ValidationResult]) -> List[Dict]:
        direction_ref_json = []
        for result in results:
            if not result.journey_was_matched() or result.matches(
                SirivmField.DIRECTION_REF
            ):
                continue
            vehicle_activity = {
                "SD ResponseTimestamp": result.sirivm_value(
                    SirivmField.RESPONSE_TIMESTAMP_SD
                ),
                "RecordedAtTime": result.sirivm_value(SirivmField.RECORDED_AT_TIME),
                "AVL data set name BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATA_FEED_NAME
                ),
                "AVL data set ID BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATA_FEED_ID
                ),
                "DatedVehicleJourneyRef in SIRI": result.sirivm_value(
                    SirivmField.DATED_VEHICLE_JOURNEY_REF
                ),
                "VehicleRef in SIRI": result.sirivm_value(SirivmField.VEHICLE_REF),
                "Timetable file name": result.misc_value(MiscFieldPPC.TXC_FILENAME),
                "Timetable data set ID BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATASET_ID
                ),
                "DepartureTime in TXC": result.misc_value(
                    MiscFieldPPC.TXC_DEPARTURE_TIME
                ),
                "DirectionRef in SIRI": result.sirivm_value(SirivmField.DIRECTION_REF),
                "Direction from JourneyPattern in TXC": result.txc_value(
                    SirivmField.DIRECTION_REF
                ),
                "SIRI XML line number": "TBD",
                "TransXChange XML line number": "TBD",
                "Error note": "\n".join(result.errors.get(ErrorCategory.DIRECTION_REF)),
            }
            vehicle_activity = {
                k: self.pretty_print(v) for k, v in vehicle_activity.items()
            }
            direction_ref_json.append(vehicle_activity)
        return direction_ref_json

    def compile_destination_ref(self, results: List[ValidationResult]) -> List[Dict]:
        destination_ref_json = []
        for result in results:
            if not result.journey_was_matched() or result.matches(
                SirivmField.DESTINATION_REF
            ):
                continue
            vehicle_activity = {
                "SD ResponseTimestamp": result.sirivm_value(
                    SirivmField.RESPONSE_TIMESTAMP_SD
                ),
                "RecordedAtTime": result.sirivm_value(SirivmField.RECORDED_AT_TIME),
                "AVL data set name BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATA_FEED_NAME
                ),
                "AVL data set ID BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATA_FEED_ID
                ),
                "DatedVehicleJourneyRef in SIRI": result.sirivm_value(
                    SirivmField.DATED_VEHICLE_JOURNEY_REF
                ),
                "VehicleRef in SIRI": result.sirivm_value(SirivmField.VEHICLE_REF),
                "Timetable file name": result.misc_value(MiscFieldPPC.TXC_FILENAME),
                "Timetable data set ID BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATASET_ID
                ),
                "DepartureTime in TXC": result.misc_value(
                    MiscFieldPPC.TXC_DEPARTURE_TIME
                ),
                "DestinationRef in SIRI": result.sirivm_value(
                    SirivmField.DESTINATION_REF
                ),
                "StopPointRef in TXC": result.txc_value(SirivmField.DESTINATION_REF),
                "SIRI XML line number": "TBD",
                "TransXChange XML line number": "TBD",
                "Error note": "\n".join(
                    result.errors.get(ErrorCategory.DESTINATION_REF)
                ),
            }
            vehicle_activity = {
                k: self.pretty_print(v) for k, v in vehicle_activity.items()
            }
            destination_ref_json.append(vehicle_activity)
        return destination_ref_json

    def compile_origin_ref(self, results: List[ValidationResult]) -> List[Dict]:
        origin_ref_json = []
        for result in results:
            if not result.journey_was_matched() or result.matches(
                SirivmField.ORIGIN_REF
            ):
                continue
            vehicle_activity = {
                "SD ResponseTimestamp": result.sirivm_value(
                    SirivmField.RESPONSE_TIMESTAMP_SD
                ),
                "RecordedAtTime": result.sirivm_value(SirivmField.RECORDED_AT_TIME),
                "AVL data set name BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATA_FEED_NAME
                ),
                "AVL data set ID BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATA_FEED_ID
                ),
                "DatedVehicleJourneyRef in SIRI": result.sirivm_value(
                    SirivmField.DATED_VEHICLE_JOURNEY_REF
                ),
                "VehicleRef in SIRI": result.sirivm_value(SirivmField.VEHICLE_REF),
                "Timetable file name": result.misc_value(MiscFieldPPC.TXC_FILENAME),
                "Timetable data set ID BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATASET_ID
                ),
                "DepartureTime in TXC": result.misc_value(
                    MiscFieldPPC.TXC_DEPARTURE_TIME
                ),
                "OriginRef in SIRI": result.sirivm_value(SirivmField.ORIGIN_REF),
                "StopPointRef in TXC": result.txc_value(SirivmField.ORIGIN_REF),
                "SIRI XML line number": "TBD",
                "TransXChange XML line number": "TBD",
                "Error note": "\n".join(result.errors.get(ErrorCategory.ORIGIN_REF)),
            }
            vehicle_activity = {
                k: self.pretty_print(v) for k, v in vehicle_activity.items()
            }
            origin_ref_json.append(vehicle_activity)
        return origin_ref_json

    def compile_block_ref(self, results: List[ValidationResult]) -> List[Dict]:
        block_ref_json = []
        for result in results:
            if not result.journey_was_matched() or result.matches(
                SirivmField.BLOCK_REF
            ):
                continue
            vehicle_activity = {
                "SD ResponseTimestamp": result.sirivm_value(
                    SirivmField.RESPONSE_TIMESTAMP_SD
                ),
                "RecordedAtTime": result.sirivm_value(SirivmField.RECORDED_AT_TIME),
                "AVL data set name BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATA_FEED_NAME
                ),
                "AVL data set ID BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATA_FEED_ID
                ),
                "DatedVehicleJourneyRef in SIRI": result.sirivm_value(
                    SirivmField.DATED_VEHICLE_JOURNEY_REF
                ),
                "VehicleRef in SIRI": result.sirivm_value(SirivmField.VEHICLE_REF),
                "Timetable file name": result.misc_value(MiscFieldPPC.TXC_FILENAME),
                "Timetable data set ID BODS": result.misc_value(
                    MiscFieldPPC.BODS_DATASET_ID
                ),
                "DepartureTime in TXC": result.misc_value(
                    MiscFieldPPC.TXC_DEPARTURE_TIME
                ),
                "BlockRef in SIRI": result.sirivm_value(SirivmField.BLOCK_REF),
                "BlockNumber in TXC": result.txc_value(SirivmField.BLOCK_REF),
                "SIRI XML line number": "TBD",
                "TransXChange XML line number": "TBD",
                "Error note": "\n".join(result.errors.get(ErrorCategory.BLOCK_REF)),
            }
            vehicle_activity = {
                k: self.pretty_print(v) for k, v in vehicle_activity.items()
            }
            block_ref_json.append(vehicle_activity)
        return block_ref_json
