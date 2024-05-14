import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from zipfile import ZipFile
import os

from transit_odp.avl.post_publishing_checks.constants import ErrorCategory, SirivmField
from transit_odp.avl.post_publishing_checks.daily.results import (
    MiscFieldPPC,
    ValidationResult,
)
from transit_odp.avl.post_publishing_checks.models import (
    MonitoredVehicleJourney,
    VehicleActivity,
)
from transit_odp.common.utils.choice_enum import ChoiceEnum
from transit_odp.common.xmlelements.exceptions import (
    NoElement,
    TooManyElements,
    XMLAttributeError,
)
from transit_odp.organisation.models import TXCFileAttributes
from transit_odp.timetables.transxchange import (
    TransXChangeDocument,
    TransXChangeElement,
)
from transit_odp.common.xmlelements.exceptions import XMLAttributeError

logger = logging.getLogger(__name__)


class DayOfWeek(ChoiceEnum):
    monday = "Monday"
    tuesday = "Tuesday"
    wednesday = "Wednesday"
    thursday = "Thursday"
    friday = "Friday"
    saturday = "Saturday"
    sunday = "Sunday"

    @classmethod
    def from_weekday_int(cls, weekday: int) -> "DayOfWeek":
        """Create DayOfWeek object from zero-based integer, compatible with
        library method date.weekday()
        """
        map = {
            0: cls.monday,
            1: cls.tuesday,
            2: cls.wednesday,
            3: cls.thursday,
            4: cls.friday,
            5: cls.saturday,
            6: cls.sunday,
        }
        return map[weekday]


@dataclass
class TxcVehicleJourney:
    vehicle_journey: TransXChangeElement
    txc_xml: TransXChangeDocument


class VehicleJourneyFinder:
    def get_vehicle_journey_ref(self, mvj: MonitoredVehicleJourney) -> Optional[str]:
        framed_vehicle_journey_ref = mvj.framed_vehicle_journey_ref
        if framed_vehicle_journey_ref is not None:
            return framed_vehicle_journey_ref.dated_vehicle_journey_ref
        return None

    def get_recorded_at_time(self, vehicle_activity: VehicleActivity) -> Optional[str]:
        vehicle_recorded_at_time = vehicle_activity.recorded_at_time
        if vehicle_recorded_at_time is not None:
            return vehicle_recorded_at_time.date()
        return None

    def check_operator_and_line_present(
        self, activity: VehicleActivity, result: ValidationResult
    ) -> bool:
        """
        Checks if OperatorRef and PublishedLineName are present in Vehicle activity
        """
        mvj = activity.monitored_vehicle_journey
        if mvj.operator_ref is None:
            result.add_error(
                ErrorCategory.GENERAL,
                "OperatorRef missing in SIRI-VM VehicleActivity",
            )
            return False

        if mvj.published_line_name is None:
            result.add_error(
                ErrorCategory.GENERAL,
                "PublishedLineName missing in SIRI-VM VehicleActivity",
            )
            return False
        return True

    def get_txc_file_metadata(
        self, noc: str, published_line_name: str, result: ValidationResult
    ) -> List[TXCFileAttributes]:
        """Get a list of published datasets with live revisions that match operator
        ref and line name.
        """
        logger.info(
            f"Get published timetable files matching NOC {noc} and PublishedLineName {published_line_name}"
        )
        txc_file_attrs = list(
            TXCFileAttributes.objects.add_revision_details()
            .filter_by_noc_and_line_name(noc, published_line_name)
            .get_active_live_revisions()
            .select_related("revision")
        )

        if len(txc_file_attrs) == 0:
            result.add_error(
                ErrorCategory.GENERAL,
                f"No published TXC files found matching NOC {noc} and "
                f"published line name {published_line_name}",
            )

        logger.debug(
            f"Found {len(txc_file_attrs)} timetable files matching NOC and LineName"
        )
        for idx, txc_file in enumerate(txc_file_attrs):
            logger.debug(
                f"{idx + 1}: Dataset id {txc_file.dataset_id} "
                f"filename {txc_file.filename}"
            )

        return txc_file_attrs

    def check_same_dataset(
        self,
        txc_file_attrs: List[TXCFileAttributes],
        mvj: MonitoredVehicleJourney,
        result: ValidationResult,
    ) -> bool:
        dataset_ids = {txc.dataset_id for txc in txc_file_attrs}
        consistent_data = len(dataset_ids) == 1
        if consistent_data:
            result.set_misc_value(MiscFieldPPC.BODS_DATASET_ID, dataset_ids.pop())
            result.set_txc_value(SirivmField.OPERATOR_REF, mvj.operator_ref)
            result.set_matches(SirivmField.OPERATOR_REF)
            result.set_txc_value(SirivmField.LINE_REF, mvj.line_ref)
            result.set_txc_value(
                SirivmField.PUBLISHED_LINE_NAME, mvj.published_line_name
            )
            result.set_transxchange_attribute(TransXChangeField.DATASET_ID, dataset_id)
            result.set_transxchange_attribute(
                TransXChangeField.MODIFICATION_DATE,
                txc_file_attrs[0].modification_datetime,
            )
            result.set_transxchange_attribute(
                TransXChangeField.FILENAME, txc_file_attrs[0].filename
            )
            result.set_transxchange_attribute(
                TransXChangeField.FILENAME, txc_file_attrs[0].filename
            )
            result.set_transxchange_attribute(
                TransXChangeField.OPERATING_PERIOD_END_DATE,
                txc_file_attrs[0].operating_period_end_date,
            )
            result.set_transxchange_attribute(
                TransXChangeField.OPERATING_PERIOD_START_DATE,
                txc_file_attrs[0].operating_period_start_date,
            )
            result.set_transxchange_attribute(
                TransXChangeField.SERVICE_CODE, txc_file_attrs[0].service_code
            )
            result.set_transxchange_attribute(TransXChangeField.LINE_REF, mvj.line_ref)
            result.set_matches(SirivmField.LINE_REF)
        else:
            logger.error("Matching TXC files belong to different datasets!\n")
            result.add_error(
                ErrorCategory.GENERAL,
                "Matched OperatorRef and PublishedLineName in more than one dataset",
            )

        return consistent_data

    def get_corresponding_timetable_xml_files(
        self, txc_file_attrs: List[TXCFileAttributes]
    ) -> List[TransXChangeDocument]:
        """Get entire XML content for each TXC object."""
        timetables: List[TransXChangeDocument] = []
        upload_file = txc_file_attrs[0].revision.upload_file
        if Path(upload_file.name).suffix == ".xml":
            with upload_file.open("rb") as fp:
                timetables.append(TransXChangeDocument(fp))
        else:
            with ZipFile(upload_file) as zin:
                txc_filenames = [txc.filename for txc in txc_file_attrs]
                for filename in zin.namelist():
                    # filename can also contains directory name
                    base_filename = os.path.basename(filename)
                    if base_filename in txc_filenames:
                        with zin.open(filename, "r") as fp:
                            timetables.append(TransXChangeDocument(fp))

        logger.info(
            f"Found {len(timetables)} out of {len(txc_file_attrs)} TXC XML files"
        )
        return timetables

    def filter_by_operating_period(
        self,
        activity_date: datetime.date,
        txc_xml: List[TransXChangeDocument],
        result: ValidationResult,
    ) -> bool:
        """Filter list of timetable files down to those in which the VehicleActivity
        date is inside the Service-level OperatingPeriod. Returns the list in place
        with non-matching timetables removed.
        """
        for idx in range(len(txc_xml) - 1, -1, -1):
            operating_period_start = txc_xml[idx].get_operating_period_start_date()
            error_msg = None
            if not operating_period_start:
                error_msg = (
                    f"Ignoring timetable {txc_xml[idx].get_file_name()} with no "
                    "OperatingPeriod"
                )
                result.add_error(ErrorCategory.GENERAL, error_msg)
                logger.info(error_msg)
            else:
                try:
                    start_date = datetime.date.fromisoformat(
                        operating_period_start[0].text
                    )
                except ValueError:
                    error_msg = (
                        f"Ignoring timetable {txc_xml[idx].get_file_name()} with "
                        "incorrectly formatted OperatingPeriod.StartDate"
                    )
                    result.add_error(ErrorCategory.GENERAL, error_msg)

                if error_msg is None:
                    operating_period_end = txc_xml[idx].get_operating_period_end_date()
                    try:
                        end_date = (
                            None
                            if not operating_period_end
                            else datetime.date.fromisoformat(
                                operating_period_end[0].text
                            )
                        )
                    except ValueError:
                        error_msg = (
                            f"Ignoring timetable {txc_xml[idx].get_file_name()} with "
                            "incorrectly formatted OperatingPeriod.EndDate"
                        )
                        result.add_error(ErrorCategory.GENERAL, error_msg)

                    if error_msg is None:
                        if start_date <= activity_date:
                            if end_date is None or end_date >= activity_date:
                                continue

                        end_date_str = "-" if end_date is None else str(end_date)
                        logger.debug(
                            f"Filtering out timetable {txc_xml[idx].get_file_name()} "
                            f"with OperatingPeriod ({start_date} to {end_date_str})"
                        )
            txc_xml.pop(idx)

        logger.info(
            f"Filtering by OperatingPeriod left {len(txc_xml)} timetable TXC " "files"
        )
        if len(txc_xml) == 0:
            result.add_error(
                ErrorCategory.GENERAL,
                "No timetables found with VehicleActivity date in OperatingPeriod",
            )
            return False

        return True

    def filter_by_journey_code(
        self,
        txc_xml: List[TransXChangeDocument],
        vehicle_journey_ref: str,
        result: ValidationResult,
    ) -> List[TxcVehicleJourney]:
        """Filter list of timetable files down to individual journeys matching the
        passed vehicle journey ref. Returns list of matching journeys coupled with their
        parent timetable file.
        """
        matching_journeys: List[TxcVehicleJourney] = []
        debug_journey_codes = []
        for timetable in txc_xml:
            try:
                vehicle_journeys = timetable.get_vehicle_journeys()
            except NoElement:
                vehicle_journeys = []
            logger.debug(
                f"Timetable {timetable} has {len(vehicle_journeys)} vehicle journeys"
            )
            for vehicle_journey in vehicle_journeys:
                try:
                    operational = vehicle_journey.get_element("Operational")
                    ticket_machine = operational.get_element("TicketMachine")
                    journey_code = ticket_machine.get_element("JourneyCode").text
                    debug_journey_codes.append(journey_code)
                except (NoElement, TooManyElements):
                    continue
                if journey_code == vehicle_journey_ref:
                    logger.debug(
                        f"Found TicketMachine/JourneyCode {journey_code} in timetable "
                        f"{timetable.get_file_name()}"
                    )
                    matching_journeys.append(
                        TxcVehicleJourney(vehicle_journey, timetable)
                    )

        logger.info(
            f"Filtering by JourneyCode gave {len(vehicle_journeys)} matching journeys"
        )
        logger.debug(
            f"In {len(txc_xml)} timetables, found JourneyCode's: {debug_journey_codes}"
        )

        if len(matching_journeys) == 0:
            result.add_error(
                ErrorCategory.GENERAL,
                f"No vehicle journeys found with JourneyCode '{vehicle_journey_ref}'",
            )

        return matching_journeys

    def filter_by_published_line_name(
        self,
        vehicle_journeys: List[TxcVehicleJourney],
        published_line_name: str,
        result: ValidationResult,
    ) -> List[TxcVehicleJourney]:
        """Filter list of timetable files down to individual journeys matching the
        passed published line name. Returns list of matching journeys coupled with their
        parent timetable file.
        """
        vehicle_journeys = [
            vj
            for vj in vehicle_journeys
            if vj.vehicle_journey.get_element("LineRef")
            and vj.vehicle_journey.get_element("LineRef").text.split(":")[3]
            == published_line_name
        ]

        if len(vehicle_journeys) == 0:
            result.add_error(
                ErrorCategory.GENERAL,
                "No published TxC files found with vehicle journey LineRef that matches with the PublishedLineName",
            )
            return None
        return vehicle_journeys

    def get_operating_profile_for_journey(
        self, vj: TxcVehicleJourney
    ) -> Optional[TransXChangeElement]:
        try:
            operating_profile = vj.vehicle_journey.get_element("OperatingProfile")
        except NoElement:
            services = vj.txc_xml.get_services()
            if len(services) == 0:
                return None
            operating_profile = services[0].get_element("OperatingProfile")
        except TooManyElements:
            return None
        return operating_profile

    def filter_by_operating_profile(
        self,
        activity_date,
        vehicle_journeys: List[TxcVehicleJourney],
        result: ValidationResult,
    ) -> bool:
        """Filter list of vehicle journeys down to those whose OperatingProfile applies
        to the VehiclActivity date. The OperatingProfile may be defined globally for
        the entire Service or individually for each VehicleJourney. Returns the list
        in place with inapplicable vehicle journeys removed.
        NOTE: Bank Holidays not yet supported
        """
        for vj in reversed(vehicle_journeys):
            operating_profile: TransXChangeElement = (
                self.get_operating_profile_for_journey(vj)
            )
            if operating_profile is None:
                logger.debug(
                    "Ignoring VehicleJourney with no operating profile: "
                    f"{vj.vehicle_journey}"
                )
                vehicle_journeys.remove(vj)
                continue
            holidays_only = operating_profile.find_anywhere("HolidaysOnly")
            if len(holidays_only) > 0:
                logger.info("Ignoring OperatingProfile with HolidaysOnly")
                vehicle_journeys.remove(vj)
                continue
            day_of_week = DayOfWeek.from_weekday_int(activity_date.weekday())
            profile_days_of_week = operating_profile.find_anywhere("DaysOfWeek")
            if len(profile_days_of_week) == 0:
                logger.info("Ignoring OperatingProfile with no DaysOfWeek")
                vehicle_journeys.remove(vj)
                continue
            specified_days = []
            for day in DayOfWeek:
                if profile_days_of_week[0].get_element_or_none(day.value) is not None:
                    specified_days.append(day)
            if day_of_week not in specified_days:
                logger.debug(
                    "Ignoring VehicleJourney with operating profile inapplicable to "
                    f"{day_of_week}"
                )
                vehicle_journeys.remove(vj)
        logger.info(
            f"Filtering by OperatingProfile left {len(vehicle_journeys)} matching "
            "journeys"
        )

        if len(vehicle_journeys) == 0:
            result.add_error(
                ErrorCategory.GENERAL,
                "No vehicle journeys found with OperatingProfile applicable to "
                "VehicleActivity date",
            )
            return False

        return True

    def filter_by_revision_number(
        self, vehicle_journeys: List[TxcVehicleJourney], result: ValidationResult
    ):
        """Filter list of vehicle journeys by revision number of the including
        timetable. Only return vehicle journeys pertaining to the file with the highest
        revision number. If more than one file has the highest revision number, return
        journeys pertaining to all those files. Returns the list in place with journeys
        from lower revision files removed.
        """
        highest_revision_number = -1
        for vj in reversed(vehicle_journeys):
            try:
                revision_number = int(vj.txc_xml.get_revision_number())
            except (ValueError, XMLAttributeError):
                vehicle_journeys.remove(vj)
                continue
            if revision_number > highest_revision_number:
                highest_revision_number = revision_number

        for vj in reversed(vehicle_journeys):
            revision_number = int(vj.txc_xml.get_revision_number())
            if revision_number < highest_revision_number:
                vehicle_journeys.remove(vj)

        if len(vehicle_journeys) == 0:
            result.add_error(
                ErrorCategory.GENERAL,
                "No RevisionNumber found in matching vehicle journeys",
            )
            return False

        return True

    def service_org_day_type(
        self, vj: TxcVehicleJourney
    ) -> Optional[TransXChangeElement]:
        try:
            xpath = ["OperatingProfile", "ServicedOrganisationDayType"]
            service_org_day_type = vj.vehicle_journey.get_element(xpath)
        except NoElement:
            return None
        except TooManyElements:
            return None
        return service_org_day_type

    def get_service_org_day_type_from_service(
        self, vj: TxcVehicleJourney
    ) -> Optional[TransXChangeElement]:
        """Find and return ServicedOrganisationDayType from service element

        Args:
            vj (TxcVehicleJourney): vehicle journey object

        Returns:
            Optional[TransXChangeElement]: Return ServicedOrganisationDayType Txc element
        """
        try:
            services = vj.txc_xml.get_services()
            vj_service_code = vj.vehicle_journey.get_text_or_default(
                "ServiceRef", default=None
            )

            for service in services:
                service_code = service.get_text_or_default("ServiceCode", default=None)
                if service_code and service_code == vj_service_code:
                    xpath = ["OperatingProfile", "ServicedOrganisationDayType"]
                    return service.get_element(xpath)
            return None
        except NoElement:
            return None
        except TooManyElements:
            return None

    def get_service_org_ref(
        self, txcElement: TransXChangeElement
    ) -> Optional[TransXChangeElement]:
        try:
            xpath = ["WorkingDays", "ServicedOrganisationRef"]
            service_org_ref = txcElement.get_text_or_default(xpath)
        except NoElement:
            return None
        except TooManyElements:
            return None
        return service_org_ref

    def get_serviced_organisations(
        self, vj: TxcVehicleJourney
    ) -> Optional[List[TransXChangeElement]]:
        try:
            service_orgs = vj.txc_xml.get_serviced_organisations()
        except NoElement:
            return []
        return service_orgs

    def get_service_code(
        self, vj: TxcVehicleJourney
    ) -> Optional[List[TransXChangeElement]]:
        try:
            service_code = vj.txc_xml.get_service_codes()
        except NoElement:
            return []
        return service_code

    def get_working_days(
        self, org: TransXChangeElement
    ) -> Optional[TransXChangeElement]:
        try:
            xpath = ["WorkingDays", "DateRange"]
            working_days = org.get_elements(xpath)
        except NoElement:
            return []
        return working_days

    def filter_by_days_of_operation(
        self,
        recorded_at_time,
        vehicle_journeys: List[TxcVehicleJourney],
        result: ValidationResult,
    ):
        for vj in reversed(vehicle_journeys):
            days_of_non_operation = None
            days_of_operation = None
            service_org_ref = None
            inside_operating_range = False
            error_msg = None

            service_org_day_type = self.service_org_day_type(
                vj
            ) or self.get_service_org_day_type_from_service(vj)

            if service_org_day_type is not None:
                days_of_non_operation: TransXChangeElement = (
                    service_org_day_type.get_element_or_none("DaysOfNonOperation")
                )
                if days_of_non_operation is not None:
                    service_org_ref = self.get_service_org_ref(days_of_non_operation)

                days_of_operation: TransXChangeElement = (
                    service_org_day_type.get_element_or_none("DaysOfOperation")
                )
                if days_of_operation is not None:
                    service_org_ref = self.get_service_org_ref(days_of_operation)

            service_orgs = self.get_serviced_organisations(vj)
            for org in service_orgs:
                org_code = org.get_text_or_default("OrganisationCode")
                if org_code == service_org_ref:
                    working_days = self.get_working_days(org)
                    for date_range in working_days:
                        start_date = date_range.get_text_or_default("StartDate")
                        if not start_date:
                            vehicle_journey_seq_no = vj.vehicle_journey[
                                "SequenceNumber"
                            ]
                            error_msg = (
                                f"Ignoring vehicle journey with sequence number "
                                f"{vehicle_journey_seq_no}, as Serviced organisation has no Start date"
                            )
                            result.add_error(ErrorCategory.GENERAL, error_msg)
                            logger.info(error_msg)
                            break

                        end_date = date_range.get_text_or_default("EndDate")
                        if not end_date:
                            vehicle_journey_seq_no = vj.vehicle_journey[
                                "SequenceNumber"
                            ]
                            error_msg = (
                                f"Ignoring vehicle journey with sequence number "
                                f"{vehicle_journey_seq_no}, as Serviced organisation has no End date"
                            )
                            result.add_error(ErrorCategory.GENERAL, error_msg)
                            logger.info(error_msg)
                            break

                        start_date_formatted = datetime.datetime.strptime(
                            start_date, "%Y-%m-%d"
                        ).date()
                        end_date_formatted = datetime.datetime.strptime(
                            end_date, "%Y-%m-%d"
                        ).date()

                        if (
                            start_date_formatted
                            <= recorded_at_time
                            <= end_date_formatted
                        ):
                            inside_operating_range = True

                    if error_msg is None:
                        if days_of_non_operation is not None and inside_operating_range:
                            vehicle_journeys.remove(vj)
                        elif (
                            days_of_operation is not None and not inside_operating_range
                        ):
                            vehicle_journeys.remove(vj)

        if len(vehicle_journeys) == 0:
            result.add_error(
                ErrorCategory.GENERAL,
                "Journeys can be found for the operating profile, but they belong to "
                "the working days of a serviced operation which is not working on the day of the journey",
            )
            return False

        return True

    def filter_by_service_code(
        self, vehicle_journeys: List[TxcVehicleJourney], result: ValidationResult
    ):
        """
        Filters vehicle journeys based on service code.
        This function checks if there are multiple vehicle journeys in a single timetable file
        or multiple vehicle journeys in timetables belonging to a single service code.
        Returns:
        bool: True if the vehicle journeys pass the filter, False otherwise.
        """
        txc_file_list = []
        service_code_list = []
        for vj in reversed(vehicle_journeys):
            txc_file_list.append(vj.txc_xml.name)
            service_code = self.get_service_code(vj)[0].text
            service_code_list.append(service_code)

        txc_file_set = set(txc_file_list)
        service_code_set = set(service_code_list)

        if len(txc_file_set) == 1:
            result.add_error(
                ErrorCategory.GENERAL,
                "Found more than one matching vehicle journey in a single timetables file belonging to a single service code",
            )
            return False
        elif len(service_code_set) == 1:
            result.add_error(
                ErrorCategory.GENERAL,
                "Found more than one matching vehicle journey in timetables belonging to a single service code",
            )
            return False
        elif len(service_code_set) > 1:
            result.errors = None
            return False
        return True

    def append_txc_revision_number(
        self, txc_xml: List[TransXChangeDocument], result: ValidationResult
    ):
        """
        Appends the revision number from the first TransXChange XML document in the given list
        and sets it in the validation result.

        Args:
            txc_xml (List[TransXChangeDocument]): A list of TransXChangeDocument objects.
            result (ValidationResult): The validation result object where the revision number will be set.

        Returns:
            None
        """
        if txc_xml:
            first_txc_xml = txc_xml[0]
            try:
                result.set_transxchange_attribute(
                    TransXChangeField.REVISION_NUMBER,
                    first_txc_xml.get_revision_number(),
                )
            except (XMLAttributeError, Exception) as exp:
                file_name = first_txc_xml.get_file_name()
                error_message = (
                    f"Revision number not found in transXchange file: {file_name}"
                )
                logger.error(f"Exception raised: {exp}")
                logger.error(error_message)

    def record_journey_match(
        self, result: ValidationResult, vehicle_journey_ref: str, vj: TxcVehicleJourney
    ):
        result.set_txc_value(SirivmField.DATED_VEHICLE_JOURNEY_REF, vehicle_journey_ref)
        result.set_matches(SirivmField.DATED_VEHICLE_JOURNEY_REF)
        result.set_journey_matched()

        result.set_misc_value(MiscFieldPPC.TXC_FILENAME, vj.txc_xml.get_file_name())
        result.set_misc_value(
            MiscFieldPPC.TXC_FILE_REVISION, vj.txc_xml.get_revision_number()
        )
        departure_time = vj.vehicle_journey.get_element_or_none("DepartureTime")
        if departure_time:
            result.set_misc_value(MiscFieldPPC.TXC_DEPARTURE_TIME, departure_time.text)

        logger.info(
            f"MATCHED {vj.txc_xml.get_file_name()} "
            f"revision {vj.txc_xml.get_revision_number()}"
        )

    def match_vehicle_activity_to_vehicle_journey(
        self,
        activity: VehicleActivity,
        result: ValidationResult,
    ) -> Optional[TxcVehicleJourney]:
        """Match a SRI-VM VehicleActivity to a TXC VehicleJourney."""
        mvj = activity.monitored_vehicle_journey

        if not self.check_operator_and_line_present(activity, result):
            return None

        matching_txc_file_attrs = self.get_txc_file_metadata(
            noc=mvj.operator_ref,
            published_line_name=mvj.published_line_name,
            result=result,
        )
        if not matching_txc_file_attrs:
            return None

        if not self.check_same_dataset(matching_txc_file_attrs, mvj, result):
            return None

        txc_xml = self.get_corresponding_timetable_xml_files(matching_txc_file_attrs)

        self.append_txc_revision_number(txc_xml, result)

        if (recorded_at_time := self.get_recorded_at_time(activity)) is None:
            result.add_error(
                ErrorCategory.GENERAL,
                "Recorded At Time missing in SIRI-VM VehicleActivity",
            )
            return None

        if not self.filter_by_operating_period(recorded_at_time, txc_xml, result):
            return None

        if (vehicle_journey_ref := self.get_vehicle_journey_ref(mvj)) is None:
            result.add_error(
                ErrorCategory.GENERAL,
                "DatedVehicleJourneyRef missing in SIRI-VM VehicleActivity",
            )
            return None

        vehicle_journeys = self.filter_by_journey_code(
            txc_xml=txc_xml, vehicle_journey_ref=vehicle_journey_ref, result=result
        )

        if not vehicle_journeys:
            return None

        vehicle_journeys = self.filter_by_published_line_name(
            vehicle_journeys=vehicle_journeys,
            published_line_name=mvj.published_line_name,
            result=result,
        )

        if not vehicle_journeys:
            return None

        if not self.filter_by_operating_profile(
            recorded_at_time, vehicle_journeys, result
        ):
            return None

        if not self.filter_by_revision_number(vehicle_journeys, result):
            return None

        if not self.filter_by_days_of_operation(
            recorded_at_time, vehicle_journeys, result
        ):
            return None

        if len(vehicle_journeys) > 1:
            if not self.filter_by_service_code(vehicle_journeys, result):
                return None

        # If we get to this point, we've matched the SIRI-VM MonitoredVehicleJourney
        # to exactly one TXC VehicleJourney. Update result to record a match.
        txc_vehicle_journey = vehicle_journeys[0]
        self.record_journey_match(result, vehicle_journey_ref, txc_vehicle_journey)
        return txc_vehicle_journey
