import datetime
import logging
import random
from typing import Dict, List, Optional, Tuple

from transit_odp.avl.post_publishing_checks.constants import (
    ErrorCategory,
    MiscFieldPPC,
    SirivmField,
)
from transit_odp.avl.post_publishing_checks.results import ValidationResult
from transit_odp.avl.post_publishing_checks.writer import (
    PostPublishingResultsJsonWriter,
)
from transit_odp.avl.proxies import AVLDataset

from .bods_client.client import BODSClient
from .bods_client.models import APIError, Siri
from .bods_client.models import TxcFile as ApiTxcFile
from .bods_client.models import TxcFileParams, TxcFileResponse
from .bods_client.models.siri import MonitoredVehicleJourney, VehicleActivity
from .pytxc.datasets import Dataset
from .pytxc.services import DayOfWeek, OperatingProfile
from .pytxc.timetables import Timetable
from .pytxc.vehicles import VehicleJourney

logger = logging.getLogger(__name__)

# For debug (temporary)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

today = datetime.date.today()

# Replace with your own API key
KEY = "b81d2408c5fa4d18416b43fdf4b0213f116a8952"


class PostPublishingChecker:
    def get_vehicle_journey_ref(self, mvj: MonitoredVehicleJourney) -> Optional[str]:
        framed_vehicle_journey_ref = mvj.framed_vehicle_journey_ref
        if framed_vehicle_journey_ref is not None:
            return framed_vehicle_journey_ref.dated_vehicle_journey_ref
        return None

    def get_vehicle_activities(
        self,
        client: BODSClient,
        feed_id: int,
        num_activities: int,
    ) -> Tuple[Dict, List[VehicleActivity]]:

        random.seed()
        sirivm_fields = {}
        feed = client.get_siri_vm_data_feed_by_id(feed_id=feed_id)
        if not isinstance(feed, bytes):
            return sirivm_fields, []

        siri = Siri.from_bytes(feed)
        sirivm_fields[SirivmField.VERSION] = siri.version
        sirivm_fields[
            SirivmField.RESPONSE_TIMESTAMP_SD
        ] = siri.service_delivery.response_timestamp
        sirivm_fields[SirivmField.PRODUCER_REF] = siri.service_delivery.producer_ref
        vmd = siri.service_delivery.vehicle_monitoring_delivery
        sirivm_fields[SirivmField.RESPONSE_TIMESTAMP_VMD] = vmd.response_timestamp
        sirivm_fields[SirivmField.REQUEST_MESSAGE_REF] = vmd.request_message_ref
        sirivm_fields[SirivmField.VALID_UNTIL] = vmd.valid_until
        sirivm_fields[SirivmField.SHORTEST_POSSIBLE_CYCLE] = vmd.shortest_possible_cycle

        vehicle_activities = vmd.vehicle_activities
        logger.info(
            f"Client returned {len(vehicle_activities)} vehicle activities for "
            f"feed {feed_id}"
        )
        if len(vehicle_activities) == 0:
            return sirivm_fields, []

        num_samples = min(num_activities, len(vehicle_activities))
        samples = random.sample(vehicle_activities, k=num_samples)

        logger.debug(
            f"Added {len(samples)} sample vehicle activities for feed id {feed_id}"
        )
        return sirivm_fields, samples

    def get_avl_feed_name(self, data_feed_id: int) -> str:
        data_feeds = AVLDataset.objects.filter(id=data_feed_id).select_related(
            "live_revision"
        )
        return "" if data_feeds.count() == 0 else data_feeds.first().revision.name

    def get_txc_file_metadata(
        self, client: BODSClient, noc: str, line_name: str
    ) -> List[ApiTxcFile]:
        logger.info(
            f"Query API for TXC files matching NOC {noc} and LineName {line_name}"
        )
        offset = 0
        limit = 25
        txc_files: List[ApiTxcFile] = []
        finished = False
        while not finished:
            params = TxcFileParams(
                noc=noc, line_name=line_name, offset=offset, limit=limit
            )
            timetable_response: TxcFileResponse = client.get_txc_files(params=params)
            if isinstance(timetable_response, APIError):
                break
            txc_files.extend(timetable_response.results)
            offset += limit
            if offset >= timetable_response.count:
                finished = True
        logger.info(f"Found {len(txc_files)} TXC files matching NOC and LineName")
        return txc_files

    def get_timetable_xml(
        self, timetable_metadata: List[ApiTxcFile], result: ValidationResult
    ) -> List[Timetable]:
        # Get entire timetable XML content for each metadata object
        timetables: List[Timetable] = []
        dataset_id = timetable_metadata[0].dataset_id
        dataset = Dataset.from_bods_id(dataset_id)
        # Look for TXC files in the dataset matching the requested timetable files
        for i in range(len(timetable_metadata)):
            found = False
            for timetable_filename, timetable in dataset.timetables.items():
                if timetable_metadata[i].filename == timetable_filename:
                    timetables.append(timetable)
                    found = True
                    break
            if found:
                logger.info(f"Found timetable file '{timetable_metadata[i].filename}'")
            else:
                error_msg = (
                    f"Failed to find timetable file '{timetable_metadata[i].filename}'"
                )
                result.add_error(ErrorCategory.GENERAL, error_msg)
                logger.error(error_msg)

        logger.info(
            f"Found {len(timetables)} out of {len(timetable_metadata)} "
            "timetable files"
        )
        return timetables

    def filter_by_operating_period(
        self, timetable_xml: List[Timetable], result: ValidationResult
    ):
        """Filter list of timetable files down to those in which today's date is inside
        the Service-level OperatingPeriod. Returns the list in place with non-matching
        timetables removed.
        """
        for idx in range(len(timetable_xml) - 1, -1, -1):
            services = timetable_xml[idx].services
            operating_period = services[0].operating_period
            if operating_period is None:
                error_msg = (
                    f"Ignoring timetable {timetable_xml[idx].header.file_name} with no "
                    "OperatingPeriod"
                )
                result.add_error(ErrorCategory.GENERAL, error_msg)
                logger.info(error_msg)
            else:
                start_date = operating_period.start_date
                if start_date <= today:
                    end_date = operating_period.end_date
                    if end_date is None or end_date >= today:
                        continue
                logger.debug(
                    f"Filtering out timetable {timetable_xml[idx].header.file_name} "
                    f"with OperatingPeriod {operating_period}"
                )
            timetable_xml.pop(idx)

    def filter_by_journey_code(
        self, timetable_xml: List[Timetable], vehicle_journey_ref: str
    ) -> List[Tuple[VehicleJourney, Timetable]]:
        """Filter list of timetable files down to individual journeys matching the
        passed vehicle journey ref. Returns list of matching journeys coupled with their
        parent timetable file.
        """
        matching_journeys: List[Tuple[VehicleJourney, Timetable]] = []
        journey_codes = []
        for timetable in timetable_xml:
            logger.debug(
                f"Timetable {timetable} has {len(timetable.vehicle_journeys)} vehicle "
                "journeys"
            )
            for vehicle_journey in timetable.vehicle_journeys:
                operational = vehicle_journey.operational
                if operational is not None:
                    ticket_machine = operational.ticket_machine
                    if ticket_machine is not None:
                        journey_codes.append(ticket_machine.journey_code)
                        if ticket_machine.journey_code == vehicle_journey_ref:
                            logger.debug(
                                "Found TicketMachine/JourneyCode "
                                f"{ticket_machine.journey_code} in timetable "
                                f"{timetable.header.file_name}"
                            )
                            matching_journeys.append((vehicle_journey, timetable))
        logger.debug(
            f"In {len(timetable_xml)} timetables, found JourneyCode's: {journey_codes}"
        )
        return matching_journeys

    def get_operating_profile_for_journey(
        self, vehicle_journey: VehicleJourney, timetable: Timetable
    ) -> OperatingProfile:
        if (operating_profile := vehicle_journey.operating_profile) is None:
            service = timetable.services[0]
            operating_profile = service.operating_profile
        return operating_profile

    def filter_by_operating_profile(
        self, vehicle_journeys: List[Tuple[VehicleJourney, Timetable]]
    ):
        """Filter list of vehicle journeys down to those whose OperatingProfile applies
        to today's date. The OperatingProfile may be defined globally for the entire
        Service or individually for each VehicleJourney. Returns the list in place with
        inapplicable vehicle journeys removed.
        NOTE: Bank Holidays not yet supported
        """
        for idx in range(len(vehicle_journeys) - 1, -1, -1):
            vehicle_journey, timetable = vehicle_journeys[idx]
            operating_profile: OperatingProfile = (
                self.get_operating_profile_for_journey(vehicle_journey, timetable)
            )
            if operating_profile.holidays_only:
                logger.info("Ignoring OperatingProfile with HolidaysOnly")
                vehicle_journeys.pop(idx)
                continue
            day_of_week_today = DayOfWeek.from_weekday_int(today.weekday())
            logger.debug(f"Today is {day_of_week_today}")
            if day_of_week_today not in operating_profile.days_of_week:
                logger.debug(
                    "Ignoring VehicleJourney with operating profile "
                    f"{operating_profile.days_of_week}"
                )
                vehicle_journeys.pop(idx)
                continue

    def filter_by_revision_number(
        self, vehicle_journeys: List[Tuple[VehicleJourney, Timetable]]
    ):
        """Filter list of vehicle journeys by revision number of the including
        timetable. Only return vehicle journeys pertaining to the file with the highest
        revision number. If more than one file has the highest revision number, return
        journeys pertaining to all those files. Returns the list in place with journeys
        from lower revision files removed.
        """
        highest_revision_number = -1
        for _, timetable in vehicle_journeys:
            if timetable.header.revision_number > highest_revision_number:
                highest_revision_number = timetable.header.revision_number

        for idx in range(len(vehicle_journeys) - 1, -1, -1):
            _, timetable = vehicle_journeys[idx]
            if timetable.header.revision_number < highest_revision_number:
                vehicle_journeys.pop(idx)

    def data_match_direction_ref(
        self,
        mvj: MonitoredVehicleJourney,
        vj: VehicleJourney,
        result: ValidationResult,
    ):
        """Match the SIRI-VM DirectionRef to the TXC DirectionRef.
        The applicable TXC Direction is found in the
        Service/StandardService/JourneyPattern element which is referenced from the
        VehicleJourney.
        """
        direction_ref = mvj.direction_ref
        if direction_ref is None:
            result.add_error(
                ErrorCategory.DIRECTION_REF, "DirectionRef not found in SIRI-VM data"
            )
        else:
            result.set_sirivm_value(SirivmField.DIRECTION_REF, direction_ref)
            direction_ref_normalised = direction_ref.lower()
            if direction_ref_normalised not in (
                "outbound",
                "inbound",
                "clockwise",
                "anticlockwise",
            ):
                result.add_error(
                    ErrorCategory.DIRECTION_REF,
                    f"Invalid value for DirectionRef: '{direction_ref}'",
                )
            else:
                matches = False
                if vj.journey_pattern_ref is not None:
                    journey_pattern = vj.journey_pattern_ref.resolve()
                    txc_direction = journey_pattern.direction
                    result.set_txc_value(SirivmField.DIRECTION_REF, txc_direction)
                    if direction_ref_normalised == "outbound":
                        matches = txc_direction in ("outbound", "inboundAndOutbound")
                    elif direction_ref_normalised == "inbound":
                        matches = txc_direction in ("inbound", "inboundAndOutbound")
                    elif direction_ref_normalised == "clockwise":
                        matches = txc_direction in ("clockwise", "circular")
                    else:
                        matches = txc_direction in ("anticlockwise", "circular")
                if matches:
                    result.set_matches(SirivmField.DIRECTION_REF)
                elif result.txc_value(SirivmField.DIRECTION_REF) is None:
                    result.add_error(
                        ErrorCategory.DIRECTION_REF,
                        "Direction not found in timetable",
                    )
                else:
                    result.add_error(
                        ErrorCategory.DIRECTION_REF,
                        "DirectionRef does not match Direction in timetable",
                    )

    def data_match_block_ref(
        self,
        mvj: MonitoredVehicleJourney,
        vj: VehicleJourney,
        result: ValidationResult,
    ):
        """Match the SIRI-VM BlockRef to the TXC BlockNumber.
        The TXC BlockNumber if present should be placed in the
        VehicleJourney/Operational/Block element.
        """
        block_ref = mvj.block_ref
        if block_ref is None:
            result.add_error(
                ErrorCategory.BLOCK_REF, "BlockRef not found in SIRI-VM VehicleActivity"
            )
        else:
            matches = False
            operational = vj.operational
            if operational is not None:
                block = operational.block
                if block is not None:
                    txc_block_number = block.block_number
                    result.set_txc_value(SirivmField.BLOCK_REF, txc_block_number)
                    matches = txc_block_number == block_ref

            if matches:
                result.set_matches(SirivmField.BLOCK_REF)
            elif result.txc_value(SirivmField.BLOCK_REF) is None:
                result.add_error(
                    ErrorCategory.BLOCK_REF,
                    "BlockNumber not found in timetable",
                )
            else:
                result.add_error(
                    ErrorCategory.BLOCK_REF,
                    "BlockRef does not match BlockNumber in timetable",
                )

    def data_match_published_line_name(
        self,
        mvj: MonitoredVehicleJourney,
        vj: VehicleJourney,
        result: ValidationResult,
    ):
        """Match the SIRI-VM PublishedLineName to the TXC LineName.
        The TXC VehicleJourney has a LineRef that references a Line element,
        containing the equivalent TXC LineName for the journey.
        """
        published_line_name = mvj.published_line_name
        if published_line_name is None:
            result.add_error(
                ErrorCategory.PUBLISHED_LINE_NAME,
                "PublishedLineName not found in SIRI-VM VehicleActivity",
            )
        else:
            matches = False
            line_ref = vj.line_ref
            if line_ref is not None:
                line = line_ref.resolve()
                txc_line_name = line.line_name
                result.set_txc_value(SirivmField.PUBLISHED_LINE_NAME, txc_line_name)
                matches = txc_line_name == published_line_name

            if matches:
                result.set_matches(SirivmField.PUBLISHED_LINE_NAME)
            elif result.txc_value(SirivmField.PUBLISHED_LINE_NAME) is None:
                result.add_error(
                    ErrorCategory.PUBLISHED_LINE_NAME,
                    "LineName not found in timetable",
                )
            else:
                result.add_error(
                    ErrorCategory.PUBLISHED_LINE_NAME,
                    "PublishedLineName does not match LineName in timetable",
                )

    def data_match_destination_ref(
        self,
        mvj: MonitoredVehicleJourney,
        vj: VehicleJourney,
        result: ValidationResult,
    ):
        """Match the SIRI-VM DestinationRef to the TXC StopPointRef.
        TXC StopPointRef is mandatory sub-element of AnnotatedStopPointRef in
        StopPoints, and is referenced from JourneyPatternTimingLink (and also
        RouteLink).
        From the VehicleJourney, we use the JourneyPatternRef to get the
        JourneyPatternSectionRefs. In the corresponding JourneyPatternSection,
        we take the final JourneyPatternTimingLink, which should contain From
        and To links, and we match against the StopPointRef of the To link.
        Note that we could also choose another route. From the VehicleJourney,
        we could take the last VehicleJourneyTimingLink and get the
        JourneyPatternTimingLink from that. The specification dictates we do
        the former.
        """
        destination_ref = mvj.destination_ref
        if destination_ref is None:
            result.add_error(
                ErrorCategory.DESTINATION_REF,
                "DestinationRef not found in SIRI-VM VehicleActivity",
            )
        else:
            matches = False
            if vj.journey_pattern_ref is not None:
                journey_pattern = vj.journey_pattern_ref.resolve()
                if journey_pattern is not None:
                    journey_pattern_section_refs = (
                        journey_pattern.journey_pattern_section_refs
                    )
                    if len(journey_pattern_section_refs) > 0:
                        journey_pattern_section = journey_pattern_section_refs[
                            0
                        ].resolve()
                        if journey_pattern_section is not None:
                            timing_links = journey_pattern_section.timing_links
                            if len(timing_links) > 0:
                                to_link = timing_links[-1].to
                                if to_link is not None:
                                    txc_stop_point_ref = to_link.stop_point_ref
                                    result.set_txc_value(
                                        SirivmField.DESTINATION_REF, txc_stop_point_ref
                                    )
                                    matches = txc_stop_point_ref == destination_ref
            if matches:
                result.set_matches(SirivmField.DESTINATION_REF)
            elif result.txc_value(SirivmField.DESTINATION_REF) is None:
                result.add_error(
                    ErrorCategory.DESTINATION_REF,
                    "Equivalent StopPointRef not found in timetable",
                )
            else:
                result.add_error(
                    ErrorCategory.DESTINATION_REF,
                    "DestinationRef does not match final StopPointRef in timetable",
                )

    def data_match_origin_ref(
        self,
        mvj: MonitoredVehicleJourney,
        vj: VehicleJourney,
        result: ValidationResult,
    ):
        """Match the SIRI-VM OriginRef to the TXC StopPointRef.
        Use equivalent logic to above for DestinationRef, except we use the
        StopPointRef of the From link of the first VehicleJourneyTimingLink.
        """
        origin_ref = mvj.origin_ref
        if origin_ref is None:
            result.add_error(
                ErrorCategory.ORIGIN_REF,
                "OriginRef not found in SIRI-VM VehicleActivity",
            )
        else:
            matches = False
            if vj.journey_pattern_ref is not None:
                journey_pattern = vj.journey_pattern_ref.resolve()
                if journey_pattern is not None:
                    journey_pattern_section_refs = (
                        journey_pattern.journey_pattern_section_refs
                    )
                    if len(journey_pattern_section_refs) > 0:
                        journey_pattern_section = journey_pattern_section_refs[
                            0
                        ].resolve()
                        if journey_pattern_section is not None:
                            timing_links = journey_pattern_section.timing_links
                            if len(timing_links) > 0:
                                from_link = timing_links[0].from_
                                if from_link is not None:
                                    txc_stop_point_ref = from_link.stop_point_ref
                                    result.set_txc_value(
                                        SirivmField.ORIGIN_REF, txc_stop_point_ref
                                    )
                                    matches = txc_stop_point_ref == origin_ref
            if matches:
                result.set_matches(SirivmField.ORIGIN_REF)
            elif result.txc_value(SirivmField.ORIGIN_REF) is None:
                result.add_error(
                    ErrorCategory.ORIGIN_REF,
                    "Equivalent StopPointRef not found in timetable",
                )
            else:
                result.add_error(
                    ErrorCategory.ORIGIN_REF,
                    "OriginRef does not match first StopPointRef in timetable",
                )

    def data_match_destination_name(
        self,
        mvj: MonitoredVehicleJourney,
        vj: VehicleJourney,
        result: ValidationResult,
    ):
        """Match the SIRI-VM DestinationName to the TXC DynamicDestinationDisplay
        or DestinationDisplay.
        TXC DynamicDestinationDisplay may be present in a From or To
        sub-element of a JourneyPatternTimingLink; if not present for all
        stops therein, a DestinationDisplay element is mandatory in the
        JourneyPattern.
        """
        destination_name = mvj.destination_name
        if destination_name is None:
            result.add_error(
                ErrorCategory.DESTINATION_NAME,
                "DestinationName not found in SIRI-VM VehicleActivity",
            )
        else:
            found = matches = False
            txc_destination_display = []
            if vj.journey_pattern_ref is not None:
                journey_pattern = vj.journey_pattern_ref.resolve()
                if journey_pattern is not None:
                    journey_pattern_section_refs = (
                        journey_pattern.journey_pattern_section_refs
                    )
                    if len(journey_pattern_section_refs) > 0:
                        journey_pattern_section = journey_pattern_section_refs[
                            0
                        ].resolve()
                        if journey_pattern_section is not None:
                            timing_links = journey_pattern_section.timing_links
                            for timing_link in timing_links:
                                from_link = timing_link.from_
                                if from_link is not None:
                                    if (
                                        from_link.dynamic_destination_display
                                        is not None
                                    ):
                                        txc_destination_display.append(
                                            from_link.dynamic_destination_display
                                        )
                                to_link = timing_link.to
                                if to_link is not None:
                                    if to_link.dynamic_destination_display is not None:
                                        txc_destination_display.append(
                                            to_link.dynamic_destination_display
                                        )
                            found = len(timing_links) > 0 and len(
                                txc_destination_display
                            ) == 2 * len(timing_links)
                            if not found:
                                result.add_error(
                                    ErrorCategory.DESTINATION_NAME,
                                    "DynamicDestinationDisplay is not fully populated "
                                    "in JourneyPatternTimingLinks in timetable",
                                )
                    if not found:
                        # If DynamicDestinationDisplay is omitted, or is used but is not
                        # present in all timing links, check DestinationDisplay
                        if journey_pattern.destination_display is not None:
                            txc_destination_display.append(
                                journey_pattern.destination_display
                            )
            matches = destination_name in txc_destination_display
            if matches:
                result.set_txc_value(SirivmField.DESTINATION_NAME, destination_name)
                result.set_matches(SirivmField.DESTINATION_NAME)
            elif len(txc_destination_display) > 0:
                result.set_txc_value(
                    SirivmField.DESTINATION_NAME, txc_destination_display[0]
                )
                result.add_error(
                    ErrorCategory.DESTINATION_NAME,
                    "DestinationName does not match any DynamicDestinationDisplay or "
                    "DestinationDisplay found in timetable",
                )
            else:
                result.add_error(
                    ErrorCategory.DESTINATION_NAME,
                    "No DynamicDestinationDisplay or DestinationDisplay found in "
                    "timetable",
                )

    def data_match(
        self,
        mvj: MonitoredVehicleJourney,
        vj: VehicleJourney,
        result: ValidationResult,
    ):
        self.data_match_direction_ref(mvj, vj, result)
        self.data_match_block_ref(mvj, vj, result)
        self.data_match_published_line_name(mvj, vj, result)
        self.data_match_destination_ref(mvj, vj, result)
        self.data_match_origin_ref(mvj, vj, result)
        self.data_match_destination_name(mvj, vj, result)

    def match_vehicle_activity_to_vehicle_journey(
        self,
        feed_id: int,
        sirivm_header: Dict,
        activities: List[VehicleActivity],
    ) -> List[ValidationResult]:
        """Match a SRI-VM VehicleActivity to a TXC VehicleJourney."""
        v2_client = BODSClient(api_key=KEY, version="v2")

        results: List[ValidationResult] = []

        for idx, activity in enumerate(activities):
            logger.info(f"FEED ID {feed_id} VEHICLE ACTIVITY #{idx}")
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

            result = ValidationResult()
            for key, value in sirivm_header.items():
                result.set_sirivm_value(key, value)
            result.set_misc_value(MiscFieldPPC.BODS_DATA_FEED_ID, feed_id)
            result.set_misc_value(
                MiscFieldPPC.BODS_DATA_FEED_NAME, self.get_avl_feed_name(feed_id)
            )

            result.set_sirivm_value(
                SirivmField.RECORDED_AT_TIME, activity.recorded_at_time
            )
            result.set_sirivm_value(
                SirivmField.ITEM_IDENTIFIER, activity.item_identifier
            )
            result.set_sirivm_value(
                SirivmField.VALID_UNTIL_TIME, activity.valid_until_time
            )
            result.set_sirivm_value(SirivmField.OPERATOR_REF, mvj.operator_ref)
            result.set_sirivm_value(SirivmField.LINE_REF, mvj.line_ref)
            result.set_sirivm_value(SirivmField.ORIGIN_NAME, mvj.origin_name)
            result.set_sirivm_value(
                SirivmField.ORIGIN_AIMED_DEPARTURE_TIME, mvj.origin_aimed_departure_time
            )
            result.set_sirivm_value(SirivmField.DIRECTION_REF, mvj.direction_ref)
            result.set_sirivm_value(SirivmField.BLOCK_REF, mvj.block_ref)
            result.set_sirivm_value(
                SirivmField.PUBLISHED_LINE_NAME, mvj.published_line_name
            )
            result.set_sirivm_value(SirivmField.DESTINATION_REF, mvj.destination_ref)
            result.set_sirivm_value(SirivmField.ORIGIN_REF, mvj.origin_ref)
            result.set_sirivm_value(SirivmField.DESTINATION_NAME, mvj.destination_name)
            result.set_sirivm_value(SirivmField.BEARING, mvj.bearing)
            result.set_sirivm_value(SirivmField.VEHICLE_REF, mvj.vehicle_ref)
            if mvj.vehicle_location is not None:
                result.set_sirivm_value(
                    SirivmField.LONGITUDE, mvj.vehicle_location.longitude
                )
                result.set_sirivm_value(
                    SirivmField.LATITUDE, mvj.vehicle_location.latitude
                )
            if (
                mvj.extensions is not None
                and mvj.extensions.vehicle_journey is not None
            ):
                result.set_sirivm_value(
                    SirivmField.DRIVER_REF, mvj.extensions.vehicle_journey.driver_ref
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

            if mvj.operator_ref is None:
                result.add_error(
                    ErrorCategory.GENERAL,
                    "OperatorRef missing in SIRI-VM VehicleActivity",
                )
                results.append(result)
                continue
            if mvj.line_ref is None:
                result.add_error(
                    ErrorCategory.GENERAL, "LineRef missing in SIRI-VM VehicleActivity"
                )
                results.append(result)
                continue
            # Get a list of refs to TXC files that match operator ref and line name.
            # Only published timetables are returned.
            timetable_metadata: List[ApiTxcFile] = self.get_txc_file_metadata(
                v2_client, noc=mvj.operator_ref, line_name=mvj.line_ref
            )
            if len(timetable_metadata) == 0:
                result.add_error(
                    ErrorCategory.GENERAL,
                    f"API returns no TXC files matching NOC {mvj.operator_ref} and "
                    f"line name {mvj.line_ref}",
                )
                results.append(result)
                continue

            consistent_data = True
            for idx in range(1, len(timetable_metadata)):
                if (
                    timetable_metadata[idx].dataset_id
                    != timetable_metadata[0].dataset_id
                ):
                    consistent_data = False
                    break

            if not consistent_data:
                logger.error("Matching TXC files belong to different datasets!\n")
                for idx in range(len(timetable_metadata)):
                    logger.error(
                        f"\tDataset id {timetable_metadata[idx].dataset_id} "
                        f"filename {timetable_metadata[idx].filename}\n"
                    )
                result.add_error(
                    ErrorCategory.GENERAL,
                    "Matched OperatorRef and LineRef in more than one dataset",
                )
                results.append(result)
                continue

            result.set_misc_value(
                MiscFieldPPC.BODS_DATASET_ID, timetable_metadata[0].dataset_id
            )
            result.set_txc_value(SirivmField.OPERATOR_REF, mvj.operator_ref)
            result.set_matches(SirivmField.OPERATOR_REF)
            result.set_txc_value(SirivmField.LINE_REF, mvj.line_ref)
            result.set_matches(SirivmField.LINE_REF)

            timetable_xml: List[Timetable] = self.get_timetable_xml(
                timetable_metadata, result
            )
            logger.info(f"Retrieved {len(timetable_xml)} timetable TXC files")
            if len(timetable_xml) == 0:
                result.add_error(
                    ErrorCategory.GENERAL, "Failed to retrieve timetable XML files"
                )
                results.append(result)
                continue

            self.filter_by_operating_period(timetable_xml, result)
            logger.info(
                f"Filtering by OperatingPeriod left {len(timetable_xml)} timetable TXC "
                "files"
            )
            if len(timetable_xml) == 0:
                result.add_error(
                    ErrorCategory.GENERAL,
                    "No timetables found with today's date in OperatingPeriod",
                )
                results.append(result)
                continue

            if (vehicle_journey_ref := self.get_vehicle_journey_ref(mvj)) is None:
                result.add_error(
                    ErrorCategory.GENERAL,
                    "DatedVehicleJourneyRef missing in SIRI-VM VehicleActivity",
                )
                results.append(result)
                continue

            vehicle_journeys = self.filter_by_journey_code(
                timetable_xml, vehicle_journey_ref
            )
            logger.info(
                f"Filtering by JourneyCode gave {len(vehicle_journeys)} matching "
                "journeys"
            )
            if len(vehicle_journeys) == 0:
                result.add_error(
                    ErrorCategory.GENERAL,
                    "No vehicle journeys found with JourneyCode "
                    f"'{vehicle_journey_ref}'",
                )
                results.append(result)
                continue

            self.filter_by_operating_profile(vehicle_journeys)
            logger.info(
                f"Filtering by OperatingProfile left {len(vehicle_journeys)} matching "
                "journeys"
            )
            if len(vehicle_journeys) == 0:
                result.add_error(
                    ErrorCategory.GENERAL,
                    "No vehicle journeys found with OperatingProfile applicable to "
                    "today",
                )
                results.append(result)
                continue

            self.filter_by_revision_number(vehicle_journeys)
            logger.info(
                f"Filtering by timetable revision number left {len(vehicle_journeys)} "
                "matching journeys"
            )

            if len(vehicle_journeys) > 1:
                logger.error(
                    f"Aborting: Found multiple ({len(vehicle_journeys)}) "
                    "VehicleJourney candidates"
                )
                result.add_error(
                    ErrorCategory.GENERAL,
                    f"Found multiple ({len(vehicle_journeys)}) VehicleJourney "
                    "candidates",
                )
                results.append(result)
                continue

            # If we get to this point, we've matched the SIRI-VM MonitoredVehicleJourney
            # to exactly one TXC VehicleJourney. Update result to record a match.
            result.set_txc_value(
                SirivmField.DATED_VEHICLE_JOURNEY_REF, vehicle_journey_ref
            )
            result.set_matches(SirivmField.DATED_VEHICLE_JOURNEY_REF)
            result.set_journey_matched()
            vehicle_journey, timetable = vehicle_journeys[0]

            result.set_misc_value(MiscFieldPPC.TXC_FILENAME, timetable.header.file_name)
            result.set_misc_value(
                MiscFieldPPC.TXC_FILE_REVISION, timetable.header.revision_number
            )
            result.set_misc_value(
                MiscFieldPPC.TXC_DEPARTURE_TIME, vehicle_journey.departure_time
            )

            logger.info(
                f"Match {timetable.header.file_name} "
                f"revision {timetable.header.revision_number}"
            )

            self.data_match(mvj, vehicle_journey, result)
            results.append(result)

        return results

    def perform_checks(
        self, activity_date: datetime.date, feed_id: int, num_activities: int = 20
    ):
        v1_client = BODSClient(api_key=KEY, version="v1")
        sirivm_header, activities = self.get_vehicle_activities(
            v1_client,
            feed_id,
            num_activities,
        )

        if len(activities) == 0:
            logger.info("Nothing to validate\n")
            return

        results = self.match_vehicle_activity_to_vehicle_journey(
            feed_id,
            sirivm_header,
            activities,
        )

        if len(results) == 0:
            logger.error("No journeys analysed!\n")
            return

        results_writer = PostPublishingResultsJsonWriter(feed_id, logger)
        results_writer.write_results(results)
