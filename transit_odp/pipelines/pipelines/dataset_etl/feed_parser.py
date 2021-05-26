import datetime
from typing import Dict

import pandas as pd
from celery.utils.log import get_task_logger
from django.core.files.base import File
from django.db import transaction

from transit_odp.naptan.models import AdminArea, Locality, StopPoint
from transit_odp.organisation.models import DatasetRevision
from transit_odp.pipelines import exceptions
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.pipelines.pipelines.dataset_etl.data_loader import DataLoader
from transit_odp.pipelines.pipelines.dataset_etl.transform import Transform
from transit_odp.pipelines.pipelines.dataset_etl.utils.etl_base import ETLUtility
from transit_odp.pipelines.pipelines.dataset_etl.utils.extract_meta_result import (
    ETLReport,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import (
    ExtractedData,
    TransformedData,
)
from transit_odp.pipelines.pipelines.dataset_etl.xml_file_parser import XmlFileParser
from transit_odp.pipelines.pipelines.dataset_etl.zip_file_parser import ZipFileParser
from transit_odp.timetables.extract import (
    TransXChangeExtractor,
    TransXChangeZipExtractor,
)
from transit_odp.timetables.loaders import TransXChangeDataLoader
from transit_odp.timetables.transformers import TransXChangeTransformer
from transit_odp.transmodel.models import Service, ServiceLink

from .utils.dataframes import (
    create_naptan_stoppoint_df_from_queryset,
    create_service_link_df_from_queryset,
)
from .utils.stats import get_extracted_stats, get_transformed_stats

logger = get_task_logger(__name__)


class FeedParser(ETLUtility):
    def __init__(self, revision: DatasetRevision, etl_task: DatasetETLTaskResult):
        self.revision = revision
        self.now = datetime.datetime.now()
        self.feed_task_result = etl_task

        self.stop_point_cache: pd.DataFrame = None
        self.service_link_cache: pd.DataFrame = None
        self.service_cache: Dict[str, Service] = None

        self.initialise_caches()

        self.extractor = XmlFileParser(self)
        self.zip_extractor = ZipFileParser(self, feed_task_result=etl_task)
        self.transformer = Transform(self)
        self.data_loader = DataLoader(self)

    def initialise_caches(self):
        """Initialise caches

        Everytime a feed is created or updated, we delete any objects created
        by that feed, i.e Service, ServicePattern, ServicePatternStop, as it is easier
        to do this and just recreate them again. However, before we do that, initialise
        the caches with the previously indexed StopPoints and ServiceLinks
        """
        logger.info("Initialising caches")

        # Fetch StopPoints and initialise cache
        stops = (
            StopPoint.objects.filter(
                service_pattern_stops__service_pattern__revision=self.revision
            )
            .distinct("id")
            .order_by("id")
        )
        self.stop_point_cache = create_naptan_stoppoint_df_from_queryset(stops)

        num_stop_points = self.stop_point_cache.shape[0]
        logger.info(f"StopPoint cache initialised with {num_stop_points} records")

        # Fetch ServiceLinks and initialise cache
        service_links = ServiceLink.objects.filter(
            service_patterns__revision=self.revision
        ).distinct()

        self.service_link_cache = create_service_link_df_from_queryset(service_links)
        num_service_links = self.service_link_cache.shape[0]
        logger.info(f"ServiceLink cache initialised with {num_service_links} records")

        # Keep a cache of created Service objects
        self.service_cache: Dict[str, Service] = {}

    def index_feed(self):
        """
        Top-level entry point for processing a Feed.
        """
        self.clean_down()
        file_field = self.revision.upload_file
        logger.info(f"Running task_index_uploaded_file {file_field}")
        self.process_file(file_field)

    def clean_down(self):
        # Initialise metadata
        self.revision.num_of_lines = None
        self.revision.admin_areas.clear()
        self.revision.localities.clear()

        self.revision.services.all().delete()
        self.revision.service_patterns.all().delete()

        self.revision.save()

    def process_file(self, file_obj: File):
        """
        Main entry point for processing various file types
        """
        extracted = self.extract(file_obj)
        self.feed_task_result.update_progress(70)

        transformed = self.transform(extracted)
        self.feed_task_result.update_progress(80)

        self.load(transformed)
        self.feed_task_result.update_progress(85)

        self.add_feed_associations()
        self.feed_task_result.update_progress(90)

    def extract(self, file_obj: File) -> ExtractedData:
        logger.info("Begin extraction step")
        filename = file_obj.name
        if filename.endswith("zip"):
            extracted = TransXChangeZipExtractor(file_obj, self.now).extract()
        elif filename.endswith("xml"):
            extracted = TransXChangeExtractor(file_obj, self.now).extract()
        else:
            raise exceptions.NoDataFoundError(filename)

        logger.info("Finished extraction step.")
        get_extracted_stats(extracted)
        return extracted

    def transform(self, extracted: ExtractedData) -> TransformedData:
        logger.info("Begin transformation step")
        transformer = TransXChangeTransformer(extracted, self.stop_point_cache)
        transformed = transformer.transform()
        logger.info("Finished transformation step.")
        stats = get_transformed_stats(transformed)

        logger.info(stats)
        return transformed

    def load(self, transformed: TransformedData) -> ETLReport:
        logger.info("Begin load step")
        loader = TransXChangeDataLoader(
            transformed,
            self.service_cache,
            self.service_link_cache,
        )
        report = loader.load(self.revision, self.now)
        with transaction.atomic():
            self.revision.transxchange_version = report.schema_version
            self.revision.num_of_lines = report.line_count
            self.revision.publisher_creation_datetime = report.creation_datetime
            self.revision.publisher_modified_datetime = report.modification_datetime
            self.revision.import_datetime = report.import_datetime
            self.revision.first_expiring_service = report.first_expiring_service
            self.revision.last_expiring_service = report.last_expiring_service
            self.revision.first_service_start = report.first_service_start
            self.revision.bounding_box = report.bounding_box
            self.revision.num_of_bus_stops = report.stop_count
            self.revision.name = report.name
            self.revision.save()
        logger.info("Finished load step in.")
        return report

    def add_feed_associations(self):
        """Roll up localities and admin_areas and populate associations on Feed table
        (this ensures we don't get duplicate records when querying through the
        ServicePattern table)"""
        localities = (
            Locality.objects.filter(service_patterns__revision=self.revision)
            .order_by("gazetteer_id")
            .distinct("gazetteer_id")
        )
        self.revision.localities.add(*localities)

        admin_areas = (
            AdminArea.objects.filter(service_patterns__revision=self.revision)
            .order_by("id")
            .distinct("id")
        )
        self.revision.admin_areas.add(*admin_areas)
