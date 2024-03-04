from datetime import datetime
import uuid

import pandas as pd
from celery.utils.log import get_task_logger
from django.core.files.base import File
from shapely.geometry import Point

from transit_odp.common.utils.geometry import construct_geometry
from transit_odp.common.utils.timestamps import extract_timestamp
from transit_odp.pipelines import exceptions
from transit_odp.pipelines.pipelines.dataset_etl.utils.etl_base import ETLUtility
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import ExtractedData
from transit_odp.timetables.dataframes import (
    journey_pattern_section_from_journey_pattern,
    journey_pattern_sections_to_dataframe,
    journey_patterns_to_dataframe,
    provisional_stops_to_dataframe,
    services_to_dataframe,
    stop_point_refs_to_dataframe,
    booking_arrangements_to_dataframe,
    vehicle_journeys_to_dataframe,
    serviced_organisations_to_dataframe,
    operating_profile_to_df,
    flexible_journey_patterns_to_dataframe,
    flexible_stop_points_from_journey_details,
)
from transit_odp.timetables.exceptions import MissingLines
from transit_odp.timetables.transxchange import TransXChangeDocument
from transit_odp.xmltoolkit.xml_toolkit import (
    XmlToolkit,
    XmlToolkitResultStatus,
    parse_xml_file,
)

logger = get_task_logger(__name__)


class XmlFileParser(ETLUtility):
    def __init__(self, feed_parser):
        self.feed_parser = feed_parser
        # TODO SJB We need to check that namespace x: doesn't already exist!
        # Document has a default namespace. The only way to use xpath in this case is
        # to create an artificial prefix
        # and then search by that prefix
        self.namespaces = {"x": "http://www.transxchange.org.uk/"}
        self.file_id = uuid.uuid4()
        self.xml_toolkit = XmlToolkit(self.namespaces)

    def extract(self, file_obj: File) -> ExtractedData:
        """
        Extracts a single xml file
        Checks that it is valid xml, contains a SchemaVersion attribute, validates
        against that schema.
        Returns extracted meta data.
        """
        doc = self.parse_document(file_obj)
        extracted = self._extract(doc, file_obj)
        return extracted

    def parse_document(self, file_obj: File):
        logger.debug("Parsing document")
        # Check the filepath parses as xml
        doc, result = parse_xml_file(file_obj.file)
        filename = file_obj.name

        if result.status == XmlToolkitResultStatus.success:
            logger.debug(f"Finished parsing document: {result.status.name}")
            return doc
        elif result.status == XmlToolkitResultStatus.invalid_file:
            raise exceptions.FileError(filename=filename)
        elif result.status == XmlToolkitResultStatus.invalid_xml:
            raise exceptions.XMLSyntaxError(filename=filename)
        else:
            raise exceptions.FileError(filename=filename)

    def check_schema(self, doc):
        return doc.getroot().get("SchemaVersion")

    def _extract(self, doc, file_obj: File) -> ExtractedData:
        """Extract data from document

        To be able to derive the Routes, we must find all the JourneyPatterns, which
        are 'TimingPatterns' in our
        nomenclature, with unique stop sequences. jp_to_jps is the jump table from
        JourneyPattern to
        JourneyPatternSection which is a section of the JourneyPattern containing a
        set of TimingLinks.

        A TimingLink is essentially a RouteLink (or ServiceLink in our model) with
        given timing information.
        When no Route/RouteLink data is provided, we generate the RouteLinks from the
        TimingLinks and create
        'route_link_ref' from a hash of the two stops' Atco codes. We then hash together
        the 'route_link_ref' of all
        the TimingLinks in the section and store this as 'route_section_hash'.

        Finally, we identify the Routes by hashing together the list of
        'route_section_hash' to form 'route_hash'.
        """
        logger.debug("Extracting data")

        filename = file_obj.name
        self.trans = TransXChangeDocument(file_obj.file)
        schema_version = self.trans.get_transxchange_version()

        # Extract Services
        logger.debug("Extracting services")
        services = self.extract_services(doc, self.file_id, filename)
        logger.debug("Finished extracting services")

        # Extract StopPoints from doc and sync with DB (StopPoints should be 'readonly'
        # within this ETL process)
        logger.debug("Extracting stop points")
        stop_points = self.extract_stop_points(doc)
        provisional_stops = self.extract_provisional_stops(doc)
        logger.debug("Finished extracted stop points")

        # Extract JourneyPattern and JourneyPatternSections
        logger.debug("Extracting journey_patterns")
        journey_patterns, jp_to_jps = self.extract_journey_patterns(doc, self.file_id)
        logger.debug("Finished extracting journey_patterns")

        # Extract JourneyPatternSections, TimingLinks and RouteLinks
        logger.debug("Extracting journey_patterns_sections")
        jp_sections, timing_links = self.extract_journey_pattern_sections(
            doc, self.file_id
        )
        logger.debug("Finished extracting journey_patterns_sections")

        # Extract VehicleJourneys
        logger.debug("Extracting vehicle_journeys")
        vehicle_journeys = self.extract_vehicle_journeys()
        logger.debug("Finished extracting vehicle_journeys")

        # Extract ServicedOrganisations
        logger.debug("Extracting serviced_organisations")
        (
            serviced_organisations,
            operating_profiles,
        ) = self.extract_serviced_organisations(self.file_id)
        logger.debug("Finished extracting serviced_organisations")

        # Extract BookingArrangements data
        logger.debug("Extracting booking_arrangements")
        booking_arrangements = self.extract_booking_arrangements(self.file_id)
        logger.debug("Finished extracting booking_arrangements")

        creation_datetime = extract_timestamp(self.trans.get_creation_date_time())
        modification_datetime = extract_timestamp(
            self.trans.get_modification_date_time()
        )

        import_datetime = self.feed_parser.now
        line_names = self.trans.get_all_line_names()
        line_count = len(line_names)
        timing_point_count = len(self.trans.get_principal_timing_points())

        # create empty DataFrames
        routes = pd.DataFrame(columns=["file_id", "route_hash"]).set_index(
            ["file_id", "route_hash"]
        )

        route_to_route_links = pd.DataFrame(
            columns=["file_id", "route_hash", "order", "route_link_ref"]
        ).set_index(["file_id", "route_hash", "order"])

        route_links = pd.DataFrame(
            columns=["file_id", "route_link_ref", "from_stop_ref", "to_stop_ref"]
        ).set_index(["file_id", "route_link_ref"])

        # extract flexible journey patterns
        logger.debug("Extracting flexible journey patterns")
        flexible_journey_details = self.extract_flexible_journey_details(self.file_id)
        logger.debug("Finished extracting flexible journey patterns")

        # extract flexible stop points from flexible journey patterns details
        flexible_stop_points = flexible_stop_points_from_journey_details(
            flexible_journey_details
        )

        return ExtractedData(
            services=services,
            stop_points=stop_points,
            flexible_stop_points=flexible_stop_points,
            provisional_stops=provisional_stops,
            journey_patterns=journey_patterns,
            flexible_journey_details=flexible_journey_details,
            jp_to_jps=jp_to_jps,
            jp_sections=jp_sections,
            booking_arrangements=booking_arrangements,
            timing_links=timing_links,
            routes=routes,
            route_to_route_links=route_to_route_links,
            route_links=route_links,
            schema_version=schema_version,
            creation_datetime=creation_datetime,
            modification_datetime=modification_datetime,
            import_datetime=import_datetime,
            line_count=line_count,
            line_names=line_names,
            timing_point_count=timing_point_count,
            stop_count=len(stop_points) + len(provisional_stops),
            vehicle_journeys=vehicle_journeys,
            serviced_organisations=serviced_organisations,
            operating_profiles=operating_profiles,
        )

    def extract_flexible_journey_details(self, file_id):
        services = self.trans.get_services()
        flexible_journey_patterns = flexible_journey_patterns_to_dataframe(services)
        if not flexible_journey_patterns.empty:
            flexible_journey_patterns["file_id"] = file_id
            flexible_journey_patterns.set_index(
                ["file_id", "journey_pattern_id"], inplace=True
            )
            return flexible_journey_patterns
        return pd.DataFrame()

    def construct_geometry(self, point: Point):
        """Functionality extracted out, proxied here to not break the API"""
        return construct_geometry(point)

    def extract_timestamp(
        self, timestamp: str, default: datetime = None, *args, **kwargs
    ):
        """Functionality extracted out, proxied here to not break the API"""
        return extract_timestamp(timestamp, default, *args, **kwargs)

    def extract_services(self, doc, file_id: int, filename):
        try:
            df = services_to_dataframe(self.trans.get_services())
        except MissingLines as err:
            message = (
                f"Service (service_code=${err.service}) is missing "
                f"line name, in file %{filename}"
            )
            raise exceptions.FileError(
                filename=filename,
                message=message,
            )

        df["file_id"] = file_id
        df.set_index(["file_id", "service_code"], inplace=True)
        return df

    def extract_stop_points(self, doc):
        refs = self.trans.get_annotated_stop_point_refs()
        return stop_point_refs_to_dataframe(refs)

    def extract_provisional_stops(self, doc):
        system = self.trans.get_location_system()
        stop_points = self.trans.get_stop_points()
        return provisional_stops_to_dataframe(stop_points, system=system)

    def extract_journey_patterns(self, doc, file_id: int):
        services = self.trans.get_services()
        journey_patterns = journey_patterns_to_dataframe(services)

        jp_to_jps = pd.DataFrame()
        if not journey_patterns.empty:
            # Create a file_id column and include as part of the index
            journey_patterns["file_id"] = file_id
            journey_patterns.set_index(["file_id", "journey_pattern_id"], inplace=True)

            # Create association table between JourneyPattern and JourneyPatternSection
            jp_to_jps = journey_pattern_section_from_journey_pattern(journey_patterns)
            journey_patterns.drop("jp_section_refs", axis=1, inplace=True)

        return journey_patterns, jp_to_jps

    def extract_vehicle_journeys(self):
        standard_vehicle_journeys = self.trans.get_all_vehicle_journeys(
            "VehicleJourney", allow_none=True
        )
        flexible_vehicle_journeys = self.trans.get_all_vehicle_journeys(
            "FlexibleVehicleJourney", allow_none=True
        )

        df_vehicle_journeys = vehicle_journeys_to_dataframe(
            standard_vehicle_journeys, flexible_vehicle_journeys
        )

        if not df_vehicle_journeys.empty:
            df_vehicle_journeys["file_id"] = self.file_id
            df_vehicle_journeys.set_index(["file_id"], inplace=True)

        return df_vehicle_journeys

    def extract_serviced_organisations(self, file_id: int):
        operating_profile_vehicle_journeys = self.trans.get_all_operating_profiles(
            "VehicleJourneys", allow_none=True
        )
        df_operating_profile = pd.DataFrame()
        if operating_profile_vehicle_journeys:
            df_operating_profile = operating_profile_to_df(
                operating_profile_vehicle_journeys
            )

        else:
            operating_profile_services = self.trans.get_all_operating_profiles(
                "Services", allow_none=True
            )
            if operating_profile_services:
                df_operating_profile = operating_profile_to_df(
                    operating_profile_services
                )

        serviced_organisations = self.trans.get_all_serviced_organisations(
            allow_none=True
        )
        df_serviced_organisation = pd.DataFrame()
        if serviced_organisations:
            df_serviced_organisation = serviced_organisations_to_dataframe(
                serviced_organisations
            )

        if not df_operating_profile.empty:
            df_operating_profile["file_id"] = file_id
            df_operating_profile.set_index(["file_id"], inplace=True)

        if not df_serviced_organisation.empty:
            df_serviced_organisation["file_id"] = file_id
            df_serviced_organisation.set_index(["file_id"], inplace=True)

        return df_serviced_organisation, df_operating_profile

    def extract_journey_pattern_sections(self, doc, file_id: int):
        sections = self.trans.get_journey_pattern_sections(allow_none=True)
        timing_links = journey_pattern_sections_to_dataframe(sections)
        jp_sections = pd.DataFrame()
        if not timing_links.empty:
            timing_links["file_id"] = file_id
            timing_links.set_index(["file_id", "jp_timing_link_id"], inplace=True)

            # Aggregate jp_sections
            jp_sections = (
                timing_links.reset_index()[["file_id", "jp_section_id"]]
                .drop_duplicates("jp_section_id")
                .set_index(["file_id", "jp_section_id"])
            )

        return jp_sections, timing_links

    def extract_booking_arrangements(self, file_id: int):
        services = self.trans.get_services()
        df = booking_arrangements_to_dataframe(services)
        df["file_id"] = file_id
        df.set_index(["file_id"], inplace=True)
        return df
