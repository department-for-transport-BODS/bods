from typing import List, Optional, Tuple

from transit_odp.avl.post_publishing_checks.constants import ErrorCategory, SirivmField
from transit_odp.avl.post_publishing_checks.daily.results import ValidationResult
from transit_odp.avl.post_publishing_checks.daily.vehicle_journey_finder import (
    TxcVehicleJourney,
)
from transit_odp.avl.post_publishing_checks.models import (
    MonitoredVehicleJourney,
    VehicleActivity,
)
from transit_odp.common.xmlelements.exceptions import NoElement
from transit_odp.timetables.transxchange import TransXChangeElement


class DataMatching:
    def data_match_direction_ref(
        self,
        mvj: MonitoredVehicleJourney,
        vj: TxcVehicleJourney,
        result: ValidationResult,
    ):
        """Match the SIRI-VM DirectionRef to the TXC DirectionRef.
        applicable TXC Direction is found in the
        Service/StandardService/JourneyPattern element which is referenced from the
        VehicleJourney.
        """
        direction_ref = mvj.direction_ref
        if direction_ref is None:
            result.add_error(
                ErrorCategory.DIRECTION_REF,
                "DirectionRef not found in SIRI-VM data",
            )
        else:
            result.set_sirivm_value(
                SirivmField.DIRECTION_REF,
                direction_ref,
                mvj.direction_ref_linenum,
            )
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
                journey_pattern_ref = vj.vehicle_journey.get_element_or_none(
                    "JourneyPatternRef"
                )
                if journey_pattern_ref is not None:
                    xpath = [
                        "Services",
                        "Service",
                        "StandardService",
                        "JourneyPattern",
                    ]
                    journey_patterns = vj.txc_xml.find_anywhere(xpath)
                    for jp in journey_patterns:
                        if jp["id"] == journey_pattern_ref.text:
                            direction_elem = jp.get_element_or_none("Direction")
                            if direction_elem is not None:
                                txc_direction = direction_elem.text
                                result.set_txc_value(
                                    SirivmField.DIRECTION_REF,
                                    txc_direction,
                                    direction_elem.line_number,
                                )
                                if direction_ref_normalised == "outbound":
                                    matches = txc_direction in (
                                        "outbound",
                                        "inboundAndOutbound",
                                    )
                                elif direction_ref_normalised == "inbound":
                                    matches = txc_direction in (
                                        "inbound",
                                        "inboundAndOutbound",
                                    )
                                elif direction_ref_normalised == "clockwise":
                                    matches = txc_direction in (
                                        "clockwise",
                                        "circular",
                                    )
                                else:
                                    matches = txc_direction in (
                                        "anticlockwise",
                                        "circular",
                                    )
                            break
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
        vj: TxcVehicleJourney,
        result: ValidationResult,
    ):
        """Match the SIRI-VM BlockRef to the TXC BlockNumber.
        The TXC BlockNumber if present should be placed in the
        VehicleJourney/Operational/Block element.
        """
        block_ref = mvj.block_ref
        if block_ref is None:
            result.add_error(
                ErrorCategory.BLOCK_REF,
                "BlockRef not found in SIRI-VM VehicleActivity",
            )
        else:
            result.set_sirivm_value(
                SirivmField.BLOCK_REF, block_ref, mvj.block_ref_linenum
            )
            try:
                operational = vj.vehicle_journey.get_element("Operational")
                block = operational.get_element("Block")
                block_number_elem = block.get_element("BlockNumber")
                txc_block_number = block_number_elem.text
                result.set_txc_value(
                    SirivmField.BLOCK_REF,
                    txc_block_number,
                    block_number_elem.line_number,
                )
                matches = txc_block_number == block_ref
            except NoElement:
                matches = False

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
        vj: TxcVehicleJourney,
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
            result.set_sirivm_value(
                SirivmField.PUBLISHED_LINE_NAME, published_line_name
            )
            matches = False
            line_ref = vj.vehicle_journey.get_element_or_none("LineRef")
            if line_ref is not None:
                lines = vj.txc_xml.get_lines()
                for line in lines:
                    if line["id"] == line_ref.text:
                        line_name_elem = line.get_element_or_none("LineName")
                        if line_name_elem is not None:
                            txc_line_name = line_name_elem.text
                            result.set_txc_value(
                                SirivmField.PUBLISHED_LINE_NAME, txc_line_name
                            )
                            matches = txc_line_name == published_line_name
                        break

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

    def get_journey_pattern_and_section_refs_from_vehicle_journey(
        self, vj: TxcVehicleJourney
    ) -> Tuple[Optional[TransXChangeElement], List[TransXChangeElement]]:
        journey_pattern_ref = vj.vehicle_journey.get_element_or_none(
            "JourneyPatternRef"
        )
        if journey_pattern_ref is not None:
            xpath = ["Services", "Service", "StandardService", "JourneyPattern"]
            journey_patterns = vj.txc_xml.find_anywhere(xpath)
            for jp in journey_patterns:
                if jp["id"] == journey_pattern_ref.text:
                    try:
                        return jp, jp.get_elements("JourneyPatternSectionRefs")
                    except NoElement:
                        return jp, []
        return None, []

    def data_match_destination_ref(
        self,
        mvj: MonitoredVehicleJourney,
        vj: TxcVehicleJourney,
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
            result.set_sirivm_value(
                SirivmField.DESTINATION_REF,
                destination_ref,
                mvj.destination_ref_linenum,
            )
            matches = False
            (
                _,
                jp_section_refs,
            ) = self.get_journey_pattern_and_section_refs_from_vehicle_journey(vj)
            if jp_section_refs:
                # It's not clear what to do if there are more than one, so since we're
                # looking for the final destination, choose the last one.
                section_ref = jp_section_refs[-1].text
                jp_sections = vj.txc_xml.get_journey_pattern_sections()
                for journey_pattern_section in jp_sections:
                    if journey_pattern_section["id"] == section_ref:
                        try:
                            timing_links = journey_pattern_section.get_elements(
                                "JourneyPatternTimingLink"
                            )
                            to_link = timing_links[-1].get_element("To")
                            stop_point_ref_elem = to_link.get_element("StopPointRef")
                            txc_stop_point_ref = stop_point_ref_elem.text
                            result.set_txc_value(
                                SirivmField.DESTINATION_REF,
                                txc_stop_point_ref,
                                stop_point_ref_elem.line_number,
                            )
                            matches = txc_stop_point_ref == destination_ref
                        except NoElement:
                            break
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
        vj: TxcVehicleJourney,
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
            result.set_sirivm_value(
                SirivmField.ORIGIN_REF, origin_ref, mvj.origin_ref_linenum
            )
            matches = False
            (
                _,
                jp_section_refs,
            ) = self.get_journey_pattern_and_section_refs_from_vehicle_journey(vj)
            if jp_section_refs:
                # It's not clear what to do if there are more than one, so since we're
                # looking for the origin, choose the first one.
                section_ref = jp_section_refs[0].text
                jp_sections = vj.txc_xml.get_journey_pattern_sections()
                for journey_pattern_section in jp_sections:
                    if journey_pattern_section["id"] == section_ref:
                        try:
                            timing_links = journey_pattern_section.get_elements(
                                "JourneyPatternTimingLink"
                            )
                            from_link = timing_links[0].get_element("From")
                            stop_point_ref_elem = from_link.get_element("StopPointRef")
                            txc_stop_point_ref = stop_point_ref_elem.text
                            result.set_txc_value(
                                SirivmField.ORIGIN_REF,
                                txc_stop_point_ref,
                                stop_point_ref_elem.line_number,
                            )
                            matches = txc_stop_point_ref == origin_ref
                        except NoElement:
                            break
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
        vj: TxcVehicleJourney,
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
            result.set_sirivm_value(SirivmField.DESTINATION_NAME, destination_name)
            txc_destination_display = set()
            (
                journey_pattern,
                jp_section_refs,
            ) = self.get_journey_pattern_and_section_refs_from_vehicle_journey(vj)
            if jp_section_refs:
                section_ref = jp_section_refs[0].text
                jp_sections = vj.txc_xml.get_journey_pattern_sections()
                timing_links = []
                for journey_pattern_section in jp_sections:
                    if journey_pattern_section["id"] == section_ref:
                        try:
                            timing_links = journey_pattern_section.get_elements(
                                "JourneyPatternTimingLink"
                            )
                        except NoElement:
                            pass
                        break

                for timing_link in timing_links:
                    from_link = timing_link.get_element_or_none("From")
                    if from_link is not None:
                        dynamic_dest_display = from_link.get_element_or_none(
                            "DynamicDestinationDisplay"
                        )
                        if dynamic_dest_display is not None:
                            txc_destination_display.add(
                                (
                                    dynamic_dest_display.text,
                                    dynamic_dest_display.line_number,
                                )
                            )
                    to_link = timing_link.get_element_or_none("To")
                    if to_link is not None:
                        dynamic_dest_display = to_link.get_element_or_none(
                            "DynamicDestinationDisplay"
                        )
                        if dynamic_dest_display is not None:
                            txc_destination_display.add(
                                (
                                    dynamic_dest_display.text,
                                    dynamic_dest_display.line_number,
                                )
                            )

            if len(txc_destination_display) == 0:
                # If DynamicDestinationDisplay is omitted, DestinationDisplay must be
                # provided
                dest_display = journey_pattern.get_element_or_none("DestinationDisplay")
                if dest_display is not None:
                    txc_destination_display.add(
                        (dest_display.text, dest_display.line_number)
                    )

            for destination_display, line_number in txc_destination_display:
                if destination_name == destination_display:
                    result.set_txc_value(
                        SirivmField.DESTINATION_NAME,
                        destination_name,
                        line_number,
                    )
                    result.set_matches(SirivmField.DESTINATION_NAME)
                    break
            if not result.matches(SirivmField.DESTINATION_NAME):
                if len(txc_destination_display) > 0:
                    (
                        destination_display,
                        line_number,
                    ) = txc_destination_display.pop()
                    result.set_txc_value(
                        SirivmField.DESTINATION_NAME,
                        destination_display,
                        line_number,
                    )
                    result.add_error(
                        ErrorCategory.DESTINATION_NAME,
                        "DestinationName does not match any "
                        "DynamicDestinationDisplay or DestinationDisplay found "
                        "in timetable",
                    )
                else:
                    result.add_error(
                        ErrorCategory.DESTINATION_NAME,
                        "No DynamicDestinationDisplay or DestinationDisplay "
                        "found in timetable",
                    )

    def data_match(
        self,
        activity: VehicleActivity,
        vj: TxcVehicleJourney,
        result: ValidationResult,
    ):
        mvj: MonitoredVehicleJourney = activity.monitored_vehicle_journey
        self.data_match_direction_ref(mvj, vj, result)
        self.data_match_block_ref(mvj, vj, result)
        self.data_match_published_line_name(mvj, vj, result)
        self.data_match_destination_ref(mvj, vj, result)
        self.data_match_origin_ref(mvj, vj, result)
        self.data_match_destination_name(mvj, vj, result)
