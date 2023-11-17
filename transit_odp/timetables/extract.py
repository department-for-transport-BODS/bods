import zipfile
from datetime import datetime

import pandas as pd
from celery.utils.log import get_task_logger
from django.core.files.base import File
from shapely.geometry import Point

from transit_odp.common.utils.geometry import construct_geometry
from transit_odp.common.utils.timestamps import extract_timestamp
from transit_odp.pipelines import exceptions
from transit_odp.pipelines.pipelines.dataset_etl.utils.aggregations import (
    aggregate_import_datetime,
    aggregate_line_count,
    aggregate_line_names,
    aggregate_schema_version,
    concat_and_dedupe,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import ExtractedData
from transit_odp.timetables.dataframes import (
    journey_pattern_section_from_journey_pattern,
    journey_pattern_sections_to_dataframe,
    journey_patterns_to_dataframe,
    provisional_stops_to_dataframe,
    services_to_dataframe,
    stop_point_refs_to_dataframe,
    flexible_journey_patterns_to_dataframe,
    booking_arrangements_to_dataframe,
)
from transit_odp.timetables.exceptions import MissingLines
from transit_odp.timetables.transxchange import TransXChangeDocument

logger = get_task_logger(__name__)


class TransXChangeExtractor:
    """An API equivalent replacement for XmlFileParser."""

    def __init__(self, file_obj: File, start_time):
        self.file_id = hash(file_obj.file)
        self.filename = file_obj.name
        self.doc = TransXChangeDocument(file_obj.file)
        self.start_time = start_time

    def extract(self) -> ExtractedData:
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
        schema_version = self.doc.get_transxchange_version()

        # Extract Services
        logger.debug("Extracting services")
        services = self.extract_services()
        logger.debug("Finished extracting services")

        # Extract StopPoints from doc and sync with DB (StopPoints should be 'readonly'
        # within this ETL process)
        logger.debug("Extracting stop points")
        stop_points = self.extract_stop_points()
        provisional_stops = self.extract_provisional_stops()
        logger.debug("Finished extracted stop points")

        # Extract JourneyPattern and JourneyPatternSections
        logger.debug("Extracting journey_patterns")
        journey_patterns, jp_to_jps = self.extract_journey_patterns()
        logger.debug("Finished extracting journey_patterns")

        # Extract JourneyPatternSections, TimingLinks and RouteLinks
        logger.debug("Extracting journey_patterns_sections")
        jp_sections, timing_links = self.extract_journey_pattern_sections()
        logger.debug("Finished extracting journey_patterns_sections")

        # Extract BookingArrangements data
        logger.debug("Extracting booking_arrangements")
        booking_arrangements = self.extract_booking_arrangements()
        logger.debug("Extracting booking_arrangements")

        creation_datetime = extract_timestamp(self.doc.get_creation_date_time())
        modification_datetime = extract_timestamp(self.doc.get_modification_date_time())

        line_names = self.doc.get_all_line_names()
        line_count = len(line_names)
        timing_point_count = len(self.doc.get_principal_timing_points())

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

        return ExtractedData(
            services=services,
            stop_points=stop_points,
            provisional_stops=provisional_stops,
            journey_patterns=journey_patterns,
            jp_to_jps=jp_to_jps,
            jp_sections=jp_sections,
            timing_links=timing_links,
            routes=routes,
            route_to_route_links=route_to_route_links,
            route_links=route_links,
            schema_version=schema_version,
            creation_datetime=creation_datetime,
            modification_datetime=modification_datetime,
            import_datetime=self.start_time,
            line_count=line_count,
            line_names=line_names,
            stop_count=len(stop_points) + len(provisional_stops),
            timing_point_count=timing_point_count,
            booking_arrangements=booking_arrangements,
        )

    def construct_geometry(self, point: Point):
        """Functionality extracted out, proxied here to not break the API"""
        return construct_geometry(point)

    def extract_timestamp(
        self, timestamp: str, default: datetime = None, *args, **kwargs
    ):
        """Functionality extracted out, proxied here to not break the API"""
        return extract_timestamp(timestamp, default, *args, **kwargs)

    def extract_services(self):
        try:
            df = services_to_dataframe(self.doc.get_services())
        except MissingLines as err:
            message = (
                f"Service (service_code=${err.service}) is missing "
                f"line name, in file %{self.filename}"
            )
            raise exceptions.FileError(
                filename=self.filename,
                message=message,
            )

        df["file_id"] = self.file_id
        df.set_index(["file_id", "service_code"], inplace=True)
        return df

    def extract_stop_points(self):
        refs = self.doc.get_annotated_stop_point_refs()
        return stop_point_refs_to_dataframe(refs)

    def extract_provisional_stops(self):
        system = self.doc.get_location_system()
        stop_points = self.doc.get_stop_points()
        return provisional_stops_to_dataframe(stop_points, system=system)

    def extract_journey_patterns(self):
        services = self.doc.get_services()
        journey_patterns = journey_patterns_to_dataframe(services)
        jp_to_jps = pd.DataFrame()
        if not journey_patterns.empty:
            # Create a file_id column and include as part of the index
            journey_patterns["file_id"] = self.file_id
            journey_patterns.set_index(["file_id", "journey_pattern_id"], inplace=True)

            # Create association table between JourneyPattern and JourneyPatternSection
            jp_to_jps = journey_pattern_section_from_journey_pattern(journey_patterns)
            journey_patterns.drop("jp_section_refs", axis=1, inplace=True)

        return journey_patterns, jp_to_jps

    def extract_journey_pattern_sections(self):
        sections = self.doc.get_journey_pattern_sections(allow_none=True)
        timing_links = journey_pattern_sections_to_dataframe(sections)

        jp_sections = pd.DataFrame()
        if not timing_links.empty:
            timing_links["file_id"] = self.file_id
            timing_links.set_index(["file_id", "jp_timing_link_id"], inplace=True)

            # Aggregate jp_sections
            jp_sections = (
                timing_links.reset_index()[["file_id", "jp_section_id"]]
                .drop_duplicates("jp_section_id")
                .set_index(["file_id", "jp_section_id"])
            )

        return jp_sections, timing_links

    def extract_booking_arrangements(self):
        services = self.doc.get_services()
        return booking_arrangements_to_dataframe(services)


class TransXChangeZipExtractor:
    def __init__(self, file_obj, start_time):
        self.file_obj = file_obj
        self.start_time = start_time

    def extract(self) -> ExtractedData:
        """
        Processes a zip file.
        """
        logger.info(f"Extracting zip file {self.file_obj.name}")
        try:
            with zipfile.ZipFile(self.file_obj.file, "r") as z:
                return self.extract_files(z)
        except zipfile.BadZipFile as e:
            raise exceptions.FileError(filename=self.file_obj.name) from e
        except exceptions.PipelineException:
            raise
        except Exception as e:
            raise exceptions.PipelineException from e

    def extract_files(self, z: zipfile.ZipFile):
        extracts = []
        filenames = [info.filename for info in z.infolist() if not info.is_dir()]
        file_count = len(filenames)
        logger.info(f"Total files in zip: {file_count}")

        for i, filename in enumerate(filenames):
            logger.info(f"Extracting: {filename}")

            if filename.endswith(".xml"):
                with z.open(filename, "r") as f:
                    file_obj = File(f, name=filename)
                    extractor = TransXChangeExtractor(file_obj, self.start_time)
                    extracted = extractor.extract()
                    extracts.append(extracted)

        return ExtractedData(
            services=concat_and_dedupe((extract.services for extract in extracts)),
            stop_points=concat_and_dedupe(
                (extract.stop_points for extract in extracts)
            ),
            provisional_stops=concat_and_dedupe(
                (extract.provisional_stops for extract in extracts)
            ),
            journey_patterns=concat_and_dedupe(
                (extract.journey_patterns for extract in extracts)
            ),
            jp_to_jps=concat_and_dedupe((extract.jp_to_jps for extract in extracts)),
            jp_sections=concat_and_dedupe(
                (extract.jp_sections for extract in extracts)
            ),
            timing_links=concat_and_dedupe(
                (extract.timing_links for extract in extracts)
            ),
            routes=concat_and_dedupe((extract.routes for extract in extracts)),
            route_to_route_links=concat_and_dedupe(
                (extract.route_to_route_links for extract in extracts)
            ),
            route_links=concat_and_dedupe(
                (extract.route_links for extract in extracts)
            ),
            schema_version=aggregate_schema_version(extracts),
            creation_datetime=None,
            modification_datetime=None,
            import_datetime=aggregate_import_datetime(extracts),
            line_count=aggregate_line_count(extracts),
            line_names=aggregate_line_names(extracts),
            timing_point_count=sum(e.timing_point_count for e in extracts),
            stop_count=len(
                concat_and_dedupe((extract.stop_points for extract in extracts))
            ),
            flexible_journey_patterns=concat_and_dedupe(
                extract.flexible_journey_patterns for extract in extracts
            ),
            booking_arrangements=concat_and_dedupe(
                (extract.booking_arrangements for extract in extracts)
            ),
        )
