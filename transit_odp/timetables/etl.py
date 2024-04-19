import datetime
from typing import Dict

from celery.utils.log import get_task_logger
from django.db import transaction

from transit_odp.pipelines import exceptions
from transit_odp.pipelines.pipelines.dataset_etl.utils.dataframes import (
    create_service_link_cache,
    create_stop_point_cache,
    get_txc_files,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.extract_meta_result import (
    ETLReport,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import (
    ExtractedData,
    TransformedData,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.stats import (
    get_extracted_stats,
    get_transformed_stats,
)
from transit_odp.timetables.extract import (
    TransXChangeExtractor,
    TransXChangeZipExtractor,
)
from transit_odp.timetables.loaders import TransXChangeDataLoader
from transit_odp.timetables.transformers import TransXChangeTransformer
from transit_odp.transmodel.models import AdminArea, Locality, Service

logger = get_task_logger(__name__)


class TransXChangePipeline:
    def __init__(self, revision):
        self.revision = revision
        self.start_time = datetime.datetime.now()
        self.file_obj = revision.upload_file

        self.stop_point_cache = create_stop_point_cache(revision.id)
        self.service_link_cache = create_service_link_cache(revision.id)
        self.service_cache: Dict[str, Service] = {}

    def run(self):
        """
        Top-level entry point for processing a Feed.
        """
        extracted = self.extract()
        transformed = self.transform(extracted)
        self.load(transformed)

    def clean_down(self):
        self.revision.num_of_lines = None
        self.revision.admin_areas.clear()
        self.revision.localities.clear()
        self.revision.services.all().delete()
        self.revision.service_patterns.all().delete()
        self.revision.save()

    def extract(self) -> ExtractedData:
        logger.info("Begin extraction step")
        filename = self.file_obj.file.name
        txc_files = get_txc_files(self.revision.id)
        if self.file_obj.file.name.endswith("zip"):
            extractor = TransXChangeZipExtractor(
                self.file_obj, self.start_time, txc_files
            )
        elif self.file_obj.file.name.endswith("xml"):
            extractor = TransXChangeExtractor(self.file_obj, self.start_time, txc_files)
        else:
            raise exceptions.NoDataFoundError(filename)

        extracted = extractor.extract()
        logger.info("Finished extraction step.")
        get_extracted_stats(extracted)
        return extracted

    def transform(self, extracted: ExtractedData) -> TransformedData:
        logger.info("Begin transformation step")
        self.clean_down()
        transformer = TransXChangeTransformer(extracted, self.stop_point_cache)
        transformed = transformer.transform()
        logger.info("Finished transformation step.")
        get_transformed_stats(transformed)
        return transformed

    def load(self, transformed: TransformedData) -> ETLReport:
        logger.info("Begin load step")
        loader = TransXChangeDataLoader(
            transformed,
            self.service_cache,
            self.service_link_cache,
        )
        report = loader.load(self.revision, self.start_time)
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
            self.revision.num_of_timing_points = report.timing_point_count
            self.revision.name = report.name
            self.revision.save()
        self.add_feed_associations()
        logger.info("Finished load step in.")
        return report

    def add_localities(self):
        """Roll up localities and populate associations on DatasetRevision table
        (this ensures we don't get duplicate records when querying through the
        ServicePattern table)"""
        localities = (
            Locality.objects.filter(service_patterns__revision=self.revision)
            .order_by("gazetteer_id")
            .distinct("gazetteer_id")
        )
        self.revision.localities.add(*localities)

    def add_admin_areas(self):
        """Roll up admin_areas and populate associations on DatasetRevision table
        (this ensures we don't get duplicate records when querying through the
        ServicePattern table)"""
        admin_areas = (
            AdminArea.objects.filter(service_patterns__revision=self.revision)
            .order_by("id")
            .distinct("id")
        )
        self.revision.admin_areas.add(*admin_areas)

    def add_feed_associations(self):
        self.add_localities()
        self.add_admin_areas()
