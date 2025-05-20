import datetime
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from zipfile import ZipFile

from lxml import etree

from transit_odp.avl.post_publishing_checks.constants import (
    ErrorCategory,
    ErrorCode,
    SirivmField,
    TransXChangeField,
)
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
            result.set_transxchange_attribute(
                TransXChangeField.FILENAME, txc_xml[idx].get_file_name()
            )
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
                ErrorCode.CODE_1_2,
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
                result.set_transxchange_attribute(
                    TransXChangeField.FILENAME, timetable.get_file_name()
                )
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
                ErrorCode.CODE_2_1,
            )

        return matching_journeys

    def filter_by_published_line_name(
        self,
        vehicle_journeys: List[TxcVehicleJourney],
        published_line_name: str,
        result: ValidationResult,
        vehicle_journey_ref: str,
    ) -> List[TxcVehicleJourney]:
        """Filter list of timetable files down to individual journeys matching the
        passed published line name. Returns list of matching journeys coupled with their
        parent timetable file.
        """
        required_vjs = []
        journey_code_operating_profile = []

        for vj in vehicle_journeys:
            result.set_transxchange_attribute(
                TransXChangeField.FILENAME, vj.txc_xml.get_file_name()
            )
            operating_profile_xml_string = (
                self.get_operating_profile_xml_tag_for_journey(vj)
            )
            journey_code_operating_profile.append(operating_profile_xml_string)
            if (
                vj.vehicle_journey.get_element("LineRef")
                and vj.vehicle_journey.get_element("LineRef").text.split(":")[3]
                == published_line_name
            ):  # add to required_vj only if published_line_name matches the last part of line ref in transxchange file
                required_vjs.append(vj)

        result.set_transxchange_attribute(
            TransXChangeField.OPERATING_PROFILES, journey_code_operating_profile
        )
        result.set_transxchange_attribute(
            TransXChangeField.JOURNEY_CODE, vehicle_journey_ref
        )

        if len(required_vjs) == 0:
            result.add_error(
                ErrorCategory.GENERAL,
                "No published TxC files found with vehicle journey LineRef that matches with the PublishedLineName",
                ErrorCode.CODE_5_1,
            )
            return None
        return required_vjs

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

    def get_operating_profile_xml_tag_for_journey(
        self, vj: TxcVehicleJourney
    ) -> Optional[TransXChangeElement]:
        """
        Retrieves the XML tag for the operating profile of a given journey.

        Args:
            vj (TxcVehicleJourney): The vehicle journey for which the operating profile XML tag is to be retrieved.

        Returns:
            Optional[TransXChangeElement]: The XML tag for the operating profile of the journey, if it exists. Otherwise, None.
        """
        operating_profile_string = None
        operating_profile_element = self.get_operating_profile_for_journey(vj)
        if operating_profile_element:
            operating_profile_string = etree.tostring(
                operating_profile_element._element, pretty_print=True
            ).decode()
        return operating_profile_string

    def filter_by_operating_profile(
        self,
        activity_date,
        vehicle_journeys: List[TxcVehicleJourney],
        result: ValidationResult,
        vehicle_journey_ref: str,
    ) -> bool:
        """Filter list of vehicle journeys down to those whose OperatingProfile applies
        to the VehiclActivity date. The OperatingProfile may be defined globally for
        the entire Service or individually for each VehicleJourney. Returns the list
        in place with inapplicable vehicle journeys removed.
        NOTE: Bank Holidays not yet supported
        """
        journey_code_operating_profile = []
        for vj in reversed(vehicle_journeys):
            result.set_transxchange_attribute(
                TransXChangeField.FILENAME, vj.txc_xml.get_file_name()
            )
            operating_profile: TransXChangeElement = (
                self.get_operating_profile_for_journey(vj)
            )
            operating_profile_xml_string = (
                self.get_operating_profile_xml_tag_for_journey(vj)
            )
            journey_code_operating_profile.append(operating_profile_xml_string)

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
            if (
                day_of_week not in specified_days
                and not self.is_vehicle_journey_operational_special_days(
                    operating_profile, activity_date, result, vj
                )
            ):
                logger.debug(
                    "Ignoring VehicleJourney with operating profile inapplicable to "
                    f"{day_of_week}"
                )
                vehicle_journeys.remove(vj)
        logger.info(
            f"Filtering by OperatingProfile left {len(vehicle_journeys)} matching "
            "journeys"
        )
        result.set_transxchange_attribute(
            TransXChangeField.OPERATING_PROFILES, journey_code_operating_profile
        )
        result.set_transxchange_attribute(
            TransXChangeField.JOURNEY_CODE, vehicle_journey_ref
        )

        if len(vehicle_journeys) == 0:
            result.add_error(
                ErrorCategory.GENERAL,
                "No vehicle journeys found with OperatingProfile applicable to "
                "VehicleActivity date",
                ErrorCode.CODE_3_1,
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

    def get_op_special_days(
        self, org: TransXChangeElement
    ) -> Optional[TransXChangeElement]:
        try:
            xpath = ["DaysOfOperation", "DateRange"]
            op_days = org.get_elements(xpath)
        except NoElement:
            return []
        return op_days

    def get_nonop_special_days(
        self, org: TransXChangeElement
    ) -> Optional[TransXChangeElement]:
        try:
            xpath = ["DaysOfNonOperation", "DateRange"]
            non_op_days = org.get_elements(xpath)
        except NoElement:
            return []
        return non_op_days

    def get_service_org_ref_and_days_of_operation(
        self, vehicle_journey: TxcVehicleJourney
    ) -> Tuple[Optional[str], Optional[TransXChangeElement]]:
        """
        Retrieve the service organization reference and days of operation or non-operation from the provided vehicle journey.

        Args:
            self: The object instance.
            vehicle_journey (TxcVehicleJourney): The vehicle journey for which the service organization reference and days of operation or non-operation are to be obtained.

        Returns:
            Tuple[Optional[str], Optional[TransXChangeElement]]: A tuple containing the service organization reference and the element representing the days of operation or non-operation, or (None, None) if not found.
        """
        service_org_ref = None
        days_of_non_operation = None
        days_of_operation = None
        service_org_ref_dict = {"days_of_operation": [], "days_of_non_operation": []}

        service_org_day_type = self.service_org_day_type(
            vehicle_journey
        ) or self.get_service_org_day_type_from_service(vehicle_journey)

        if service_org_day_type is not None:
            days_of_non_operation: TransXChangeElement = (
                service_org_day_type.get_element_or_none("DaysOfNonOperation")
            )
            if days_of_non_operation is not None:
                service_org_ref = self.get_service_org_ref(days_of_non_operation)
                service_org_ref_dict["days_of_non_operation"].append(service_org_ref)

            days_of_operation: TransXChangeElement = (
                service_org_day_type.get_element_or_none("DaysOfOperation")
            )
            if days_of_operation is not None:
                service_org_ref = self.get_service_org_ref(days_of_operation)
                service_org_ref_dict["days_of_operation"].append(service_org_ref)

        return (
            service_org_ref,
            service_org_ref_dict,
        )

    def get_service_orgs_working_days_start_end_date(
        self,
        org: TransXChangeElement,
        result: ValidationResult,
        recorded_at: datetime.date,
        vj: TxcVehicleJourney,
    ) -> bool:
        """Method to find out the recorded_at_time is present in the start date or end date
        Provided in the service organisation of TXC file

        Args:
            org (TransXChangeElement): _description_
            result (ValidationResult): validation results class for error collection
            recorded_at (datetime.date): date on which vehicle activity was recorded

        Returns:
            bool: True means recorded_at is between the dates given in service organisation
        """

        working_days = self.get_working_days(org)
        for date_range in working_days:
            start_date = date_range.get_text_or_default("StartDate")
            if not start_date:
                vehicle_journey_seq_no = vj.vehicle_journey["SequenceNumber"]
                error_msg = (
                    f"Ignoring vehicle journey with sequence number "
                    f"{vehicle_journey_seq_no}, as Serviced organisation has no Start date"
                )
                result.add_error(ErrorCategory.GENERAL, error_msg)
                logger.info(error_msg)
                break

            end_date = date_range.get_text_or_default("EndDate")
            if not end_date:
                vehicle_journey_seq_no = vj.vehicle_journey["SequenceNumber"]
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
            end_date_formatted = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            if start_date_formatted <= recorded_at <= end_date_formatted:
                return True
        return False

    def is_vehicle_journey_operational_special_days(
        self,
        operating_profile: TransXChangeElement,
        recorded_at: datetime.date,
        result: ValidationResult,
        vj: TxcVehicleJourney,
    ) -> bool:
        """Method to find out the recorded_at_time is present in the start date or end date
        provided in the SepecialDaysOperation DaysOfOperation date range

        Args:
            org (TransXChangeElement): _description_
            result (ValidationResult): validation results class for error collection
            recorded_at (datetime.date): date on which vehicle activity was recorded

        Returns:
            bool: True means recorded_at is between the dates given in service organisation
        """
        op_working_days = self.get_op_special_days(operating_profile)
        for date_range in op_working_days:
            start_date = date_range.get_text_or_default("StartDate")
            if not start_date:
                vehicle_journey_seq_no = vj.vehicle_journey["SequenceNumber"]
                error_msg = (
                    f"Ignoring vehicle journey with sequence number "
                    f"{vehicle_journey_seq_no}, as DaysOfOperation has no Start date"
                )
                result.add_error(ErrorCategory.GENERAL, error_msg)
                logger.info(error_msg)
                break

            end_date = date_range.get_text_or_default("EndDate")
            if not end_date:
                vehicle_journey_seq_no = vj.vehicle_journey["SequenceNumber"]
                error_msg = (
                    f"Ignoring vehicle journey with sequence number "
                    f"{vehicle_journey_seq_no}, as DaysOfOperation has no End date"
                )
                result.add_error(ErrorCategory.GENERAL, error_msg)
                logger.info(error_msg)
                break

            start_date_formatted = datetime.datetime.strptime(
                start_date, "%Y-%m-%d"
            ).date()
            end_date_formatted = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            if start_date_formatted <= recorded_at <= end_date_formatted:
                return True
        return False

    def is_vehicle_journey_nonoperational_special_days(
        self,
        operating_profile: TransXChangeElement,
        recorded_at: datetime.date,
        result: ValidationResult,
        vj: TxcVehicleJourney,
    ) -> bool:
        """Method to find out the recorded_at_time is present in the start date or end date
        Provided in the service organisation of TXC file

        Args:
            org (TransXChangeElement): _description_
            result (ValidationResult): validation results class for error collection
            recorded_at (datetime.date): date on which vehicle activity was recorded

        Returns:
            bool: True means recorded_at is between the dates given in service organisation
        """
        non_op_working_days = self.get_nonop_special_days(operating_profile)
        for date_range in non_op_working_days:
            start_date = date_range.get_text_or_default("StartDate")
            if not start_date:
                vehicle_journey_seq_no = vj.vehicle_journey["SequenceNumber"]
                error_msg = (
                    f"Ignoring vehicle journey with sequence number "
                    f"{vehicle_journey_seq_no}, as DaysOfNonOperation has no Start date"
                )
                result.add_error(ErrorCategory.GENERAL, error_msg)
                logger.info(error_msg)
                break

            end_date = date_range.get_text_or_default("EndDate")
            if not end_date:
                vehicle_journey_seq_no = vj.vehicle_journey["SequenceNumber"]
                error_msg = (
                    f"Ignoring vehicle journey with sequence number "
                    f"{vehicle_journey_seq_no}, as DaysOfNonOperation has no End date"
                )
                result.add_error(ErrorCategory.GENERAL, error_msg)
                logger.info(error_msg)
                break

            start_date_formatted = datetime.datetime.strptime(
                start_date, "%Y-%m-%d"
            ).date()
            end_date_formatted = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            if start_date_formatted <= recorded_at <= end_date_formatted:
                return True
        return False

    def filter_by_days_of_operation(
        self,
        recorded_at_time: datetime.date,
        vehicle_journeys: List[TxcVehicleJourney],
        result: ValidationResult,
    ) -> bool:
        """Filter vehicle journies based on days of operation in ServicedOrganisations
        DaysOfNonOperations gets priority over DaysOfOperation in cased both elements are present in
        Operating profile
        if DaysOfNonOperation is present and recorded_at_time is BETWEEN start date and end date for
        ServicedOrganisation, VehicleJourney will be removed from the list

        if DaysOfOperation is present and recorded_at_time is OUTSIDE start date and end date for
        ServicedOrganisation, VehicleJourney will be removed from the list

        Args:
            recorded_at_time (datetime.date): vehicle movement recorded date
            vehicle_journeys (List[TxcVehicleJourney]): list of vehicle journeys
            result (ValidationResult): result class for recording errors

        Returns:
            bool:
        """
        for vj in reversed(vehicle_journeys):

            (
                service_org_ref,
                service_org_ref_dict,
            ) = self.get_service_org_ref_and_days_of_operation(vj)
            service_orgs = self.get_serviced_organisations(vj)

            service_orgs_dict = {
                org.get_text_or_default("OrganisationCode"): org for org in service_orgs
            }

            if len(service_org_ref_dict["days_of_non_operation"]) > 0:
                for service_org_ref in service_org_ref_dict["days_of_non_operation"]:
                    if service_org_ref not in service_orgs_dict:
                        continue
                    org = service_orgs_dict[service_org_ref]
                    if self.get_service_orgs_working_days_start_end_date(
                        org, result, recorded_at_time, vj
                    ):
                        vehicle_journeys.remove(vj)

            elif len(service_org_ref_dict["days_of_operation"]) > 0:
                for service_org_ref in service_org_ref_dict["days_of_operation"]:
                    if service_org_ref not in service_orgs_dict:
                        continue
                    org = service_orgs_dict[service_org_ref]

                    if not self.get_service_orgs_working_days_start_end_date(
                        org, result, recorded_at_time, vj
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
        self,
        vehicle_journeys: List[TxcVehicleJourney],
        result: ValidationResult,
        vehicle_journey_ref: str,
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
        journey_code_operating_profile_service_org = []

        for vj in reversed(vehicle_journeys):
            result.set_transxchange_attribute(
                TransXChangeField.FILENAME, vj.txc_xml.get_file_name()
            )
            service_org_ref, _ = self.get_service_org_ref_and_days_of_operation(
                vj
            )
            operating_profile_xml_string = (
                self.get_operating_profile_xml_tag_for_journey(vj)
            )
            journey_code = vj.vehicle_journey.get_element(
                ["Operational", "TicketMachine", "JourneyCode"]
            )
            journey_code_text = journey_code.text if journey_code else journey_code
            journey_code_operating_profile_service_org.append(
                {
                    "operating_profile_xml_string": operating_profile_xml_string,
                    "service_organisation_xml_str": service_org_ref,
                    "service_organisation_day_operating": service_org_ref,
                    "journey_code": journey_code_text,
                }
            )

            txc_file_list.append(vj.txc_xml.name)
            service_code = self.get_service_code(vj)[0].text
            service_code_list.append(service_code)

        txc_file_set = set(txc_file_list)
        service_code_set = set(service_code_list)

        result.set_transxchange_attribute(
            TransXChangeField.SERVICE_ORGANISATION_DETAILS,
            journey_code_operating_profile_service_org,
        )
        result.set_transxchange_attribute(
            TransXChangeField.JOURNEY_CODE, vehicle_journey_ref
        )

        if len(txc_file_set) == 1:
            result.add_error(
                ErrorCategory.GENERAL,
                "Found more than one matching vehicle journey in a single timetables file belonging to a single service code",
                ErrorCode.CODE_6_2_A,
            )
            return False
        elif len(service_code_set) == 1:
            result.add_error(
                ErrorCategory.GENERAL,
                "Found more than one matching vehicle journey in timetables belonging to a single service code",
                ErrorCode.CODE_6_2_B,
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
            vehicle_journey_ref=vehicle_journey_ref,
        )

        if not vehicle_journeys:
            return None

        if not self.filter_by_operating_profile(
            recorded_at_time, vehicle_journeys, result, vehicle_journey_ref
        ):
            return None

        if not self.filter_by_revision_number(vehicle_journeys, result):
            return None

        if not self.filter_by_days_of_operation(
            recorded_at_time, vehicle_journeys, result
        ):
            return None

        if not self.filter_by_special_days_of_operation(
            recorded_at_time, vehicle_journeys, result
        ):
            return None

        if len(vehicle_journeys) > 1:
            if not self.filter_by_service_code(
                vehicle_journeys, result, vehicle_journey_ref
            ):
                return None

        # If we get to this point, we've matched the SIRI-VM MonitoredVehicleJourney
        # to exactly one TXC VehicleJourney. Update result to record a match.
        txc_vehicle_journey = vehicle_journeys[0]
        self.record_journey_match(result, vehicle_journey_ref, txc_vehicle_journey)
        return txc_vehicle_journey

    def filter_by_special_days_of_operation(
        self,
        recorded_at_time: datetime.date,
        vehicle_journeys: List[TxcVehicleJourney],
        result: ValidationResult,
    ) -> bool:
        """Filter vehicle journeys based on days of SpecialDaysOperation DaysOfNonOperations
        date range.
        if DaysOfNonOperation is present and recorded_at_time is BETWEEN start date and end date,
        VehicleJourney will be removed from the list

        if DaysOfOperation is present and recorded_at_time is OUTSIDE start date and end date for
        ServicedOrganisation, VehicleJourney will be removed from the list

        Args:
            recorded_at_time (datetime.date): vehicle movement recorded date
            vehicle_journeys (List[TxcVehicleJourney]): list of vehicle journeys
            result (ValidationResult): result class for recording errors

        Returns:
            bool:
        """
        for vj in reversed(vehicle_journeys):
            operating_profile = self.get_operating_profile_for_journey(vj)
            is_vj_nonoperational_on_recorded_at_time = (
                self.is_vehicle_journey_nonoperational_special_days(
                    operating_profile, recorded_at_time, result, vj
                )
            )

            if is_vj_nonoperational_on_recorded_at_time:
                vehicle_journeys.remove(vj)

        if len(vehicle_journeys) == 0:
            result.add_error(
                ErrorCategory.GENERAL,
                "Journeys can be found for the operating profile, but they belong to "
                "the SpecialDaysOperation DaysOfNonOperation date range",
            )
            return False

        return True
