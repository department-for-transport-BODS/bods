import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List

from django.core.files.base import ContentFile

from transit_odp.avl.models import PostPublishingCheckReport, PPCReportType
from transit_odp.avl.post_publishing_checks.constants import (
    SIRIVM_TO_TXC_MAP,
    ErrorCategory,
    MiscFieldPPC,
    SirivmField,
    TransXChangeField,
    ErrorCode,
)
from transit_odp.avl.post_publishing_checks.daily.results import ValidationResult
from transit_odp.common.constants import UTF8

logger = logging.getLogger(__name__)


class FieldStat:
    def __init__(self, sirivm_field: SirivmField):
        self.sirivm_field = sirivm_field
        self.count_present = 0
        self.count_matches = 0


class PostPublishingResultsJsonWriter:
    def __init__(self, activity_date: datetime.date, feed_id: int):
        self.activity_date = activity_date
        self.feed_id = feed_id
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
        filename = (
            f"day_{self.activity_date.strftime('%d_%m_%Y')}_"
            f"feed_{self.feed_id}.json"
        )
        content_file = ContentFile(
            json.dumps(self.json_report).encode(UTF8), name=filename
        )
        total_analysed = len(results)

        ppc_report, created = PostPublishingCheckReport.objects.get_or_create(
            dataset_id=self.feed_id,
            created=self.activity_date,
            granularity=PPCReportType.DAILY,
        )
        if created:
            ppc_report.file = content_file
            ppc_report.vehicle_activities_analysed = total_analysed
            ppc_report.vehicle_activities_completely_matching = self.complete_matches
            ppc_report.save()
        else:
            logger.warning(
                "PPC report not created: One already exists for feed id "
                f"{self.feed_id} on {self.activity_date}"
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
        self.json_report["ErrorData"] = self.compile_error_data(results)
        self.json_report["DirectionRef"] = self.compile_direction_ref(results)
        self.json_report["DestinationRef"] = self.compile_destination_ref(results)
        self.json_report["OriginRef"] = self.compile_origin_ref(results)
        self.json_report["BlockRef"] = self.compile_block_ref(results)

    def compile_error_data(self, results: List[ValidationResult]) -> dict:
        """
        Compiles error data from a list of result objects into a dictionary of error results.

        Args:
            results (list): A list of result objects containing error information.

        Returns:
            dict: A dictionary where keys are error codes and values are lists of error data dictionaries.

        Each error data dictionary contains the following keys:
            - 'Dataset ID': The dataset ID associated with the error.
            - 'Filename': The filename associated with the error.
            - 'Modification date': The modification date associated with the error.
            - 'Revision number': The revision number associated with the error.
            - 'Operation period start date': The start date of the operating period associated with the error.
            - 'Operating period end date': The end date of the operating period associated with the error.
            Additional keys depend on the specific error code:
                - For error codes 1.2 and 2.1: No additional keys.
                - For error code 3.1: 'Journey Code', 'Operating Profile', and 'Service Code'.
                - For error code 5.1: 'Journey Code', 'Operating Profile', 'Service Code', and 'LineRef'.
                - For error codes 6.2 A and 6.2 C: 'Journey Code', 'Operating Profile',
                  'Serviced organisation for that journey', and 'Serviced organisation operating on that day'.

        """
        error_results_json = {}

        for result in results:
            error_codes = result.errors_code
            txc_data_common = {
                "Dataset ID": result.transxchange_attribute(
                    TransXChangeField.DATASET_ID
                ),
                "Filename": result.transxchange_attribute(TransXChangeField.FILENAME),
                "Modification date": result.transxchange_attribute(
                    TransXChangeField.MODIFICATION_DATE
                ),
                "Revision number": result.transxchange_attribute(
                    TransXChangeField.REVISION_NUMBER
                ),
                "Operation period start date": result.transxchange_attribute(
                    TransXChangeField.OPERATING_PERIOD_START_DATE
                ),
                "Operating period end date": result.transxchange_attribute(
                    TransXChangeField.OPERATING_PERIOD_END_DATE
                ),
            }
            for error_code, should_process in error_codes.items():
                if not should_process:
                    continue

                if error_code in (ErrorCode.CODE_1_2.name, ErrorCode.CODE_2_1.name):
                    txc_data = txc_data_common.copy()
                    pretty_printed_data = {
                        k: self.pretty_print(v) for k, v in txc_data.items()
                    }
                    error_results_json.setdefault(error_code, []).append(
                        pretty_printed_data
                    )

                elif error_code == ErrorCode.CODE_3_1.name:
                    operating_profiles = result.transxchange_attribute(
                        TransXChangeField.OPERATING_PROFILES
                    )
                    for operating_profile in operating_profiles:
                        txc_data = txc_data_common.copy()
                        txc_data.update(
                            {
                                "Journey Code": result.transxchange_attribute(
                                    TransXChangeField.JOURNEY_CODE
                                ),
                                "Operating Profile": operating_profile,
                                "Service Code": result.transxchange_attribute(
                                    TransXChangeField.SERVICE_CODE
                                ),
                            }
                        )
                        pretty_printed_data = {
                            k: self.pretty_print(v) for k, v in txc_data.items()
                        }
                        error_results_json.setdefault(error_code, []).append(
                            pretty_printed_data
                        )

                elif error_code == ErrorCode.CODE_5_1.name:
                    operating_profiles = result.transxchange_attribute(
                        TransXChangeField.OPERATING_PROFILES
                    )
                    for operating_profile in operating_profiles:
                        txc_data = txc_data_common.copy()
                        txc_data.update(
                            {
                                "Journey Code": result.transxchange_attribute(
                                    TransXChangeField.JOURNEY_CODE
                                ),
                                "Operating Profile": operating_profile,
                                "Service Code": result.transxchange_attribute(
                                    TransXChangeField.SERVICE_CODE
                                ),
                                "LineRef": result.transxchange_attribute(
                                    TransXChangeField.LINE_REF
                                ),
                            }
                        )
                        pretty_printed_data = {
                            k: self.pretty_print(v) for k, v in txc_data.items()
                        }
                        error_results_json.setdefault(error_code, []).append(
                            pretty_printed_data
                        )

                elif error_code in (
                    ErrorCode.CODE_6_2_A.name,
                    ErrorCode.CODE_6_2_C.name,
                ):
                    service_org_details = result.transxchange_attribute(
                        TransXChangeField.SERVICE_ORGANISATION_DETAILS
                    )
                    for service_org_detail in service_org_details:
                        txc_data = txc_data_common.copy()
                        txc_data.update(
                            {
                                "Journey Code": service_org_detail.get(
                                    "journey_code", "-"
                                ),
                                "Operating Profile": service_org_detail.get(
                                    "operating_profile_xml_string", "-"
                                ),
                                "Serviced organisation for that journey": service_org_detail.get(
                                    "service_organisation_xml_str", "-"
                                ),
                                "Serviced organisation operating on that day": service_org_detail.get(
                                    "service_organisation_day_operating", "-"
                                ),
                                "Service Code": result.transxchange_attribute(
                                    TransXChangeField.SERVICE_CODE
                                ),
                            }
                        )
                        pretty_printed_data = {
                            k: self.pretty_print(v) for k, v in txc_data.items()
                        }
                        error_results_json.setdefault(error_code, []).append(
                            pretty_printed_data
                        )
        return error_results_json

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
                        if field.sirivm_field != SirivmField.BLOCK_REF:
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
            if len(results) == 0:
                percent_populated = self.pretty_print(None)
                percent_matched = self.pretty_print(None)
            else:
                percent_populated = (
                    str(round(field.count_present * 100 / len(results), 1)) + "%"
                )
                percent_matched = (
                    str(round(field.count_matches * 100 / len(results), 1)) + "%"
                )
            field_json = {
                "SIRI field": field.sirivm_field.value,
                "TXC match field": SIRIVM_TO_TXC_MAP[field.sirivm_field],
                "Total vehicleActivities analysed": len(results),
                "Total count of SIRI fields populated": field.count_present,
                "%populated": percent_populated,
                "Successful match with TXC": str(field.count_matches),
                "%match": percent_matched,
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
                error_code = [
                    err_code
                    for err_code, should_process in result.errors_code.items()
                    if should_process
                ]
                error_code = " ".join(error_code).strip()
                error_note = "\n".join(result.errors.get(ErrorCategory.GENERAL))
                error_note = (
                    f"{error_note} [{error_code}]" if error_code else error_note
                )

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
                    "TXC": error_note,
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
                "SIRI XML line number": result.sirivm_line_number(
                    SirivmField.DIRECTION_REF
                ),
                "TransXChange XML line number": result.txc_line_number(
                    SirivmField.DIRECTION_REF
                ),
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
                "SIRI XML line number": result.sirivm_line_number(
                    SirivmField.DESTINATION_REF
                ),
                "TransXChange XML line number": result.txc_line_number(
                    SirivmField.DESTINATION_REF
                ),
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
                "SIRI XML line number": result.sirivm_line_number(
                    SirivmField.ORIGIN_REF
                ),
                "TransXChange XML line number": result.txc_line_number(
                    SirivmField.ORIGIN_REF
                ),
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
                "SIRI XML line number": result.sirivm_line_number(
                    SirivmField.BLOCK_REF
                ),
                "TransXChange XML line number": result.txc_line_number(
                    SirivmField.BLOCK_REF
                ),
                "Error note": "\n".join(result.errors.get(ErrorCategory.BLOCK_REF)),
            }
            vehicle_activity = {
                k: self.pretty_print(v) for k, v in vehicle_activity.items()
            }
            block_ref_json.append(vehicle_activity)
        return block_ref_json
