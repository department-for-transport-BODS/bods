import os
import tempfile
import zipfile
from typing import List

from celery.utils.log import get_task_logger
from django.core.files.base import File

from transit_odp.pipelines import exceptions
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.pipelines.pipelines.dataset_etl.utils.aggregations import (
    aggregate_import_datetime,
    aggregate_line_count,
    aggregate_line_names,
    aggregate_schema_version,
    concat_and_dedupe,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.etl_base import ETLUtility
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import ExtractedData

logger = get_task_logger(__name__)


class ZipFileParser(ETLUtility):
    def __init__(self, feed_parser, feed_task_result: DatasetETLTaskResult):
        self.feed_parser = feed_parser
        self.feed_task_result = feed_task_result

    def unzip(self, file_obj: File):
        """
        Unzip a zip file.
        Caller is responsible for deleting the tmpdirname
        """
        zip_ref = zipfile.ZipFile(file_obj.file, "r")
        tmpdirname = tempfile.TemporaryDirectory()
        zip_ref.extractall(tmpdirname.name)

        # Now index into the directory, computing rollup stats
        files = os.listdir(tmpdirname.name)

        return tmpdirname, files

    def extract(self, file_obj: File) -> ExtractedData:
        """
        Processes a zip file.
        File is unzipped to a temporary directory. Each unzipped file is then further
        processed as an xml file.
        """
        logger.info(f"Extracting zip file {file_obj.name}")
        try:
            with zipfile.ZipFile(file_obj.file, "r") as z:
                return self.extract_files(z)
        except zipfile.BadZipFile as e:
            raise exceptions.FileError(filename=file_obj.name) from e
        except exceptions.PipelineException:
            # filter out PipelineException exception so we can catch and
            # wrap non-PipelineExceptions below
            raise
        except Exception as e:
            raise PipelineException from e

    def extract_files(self, z: zipfile.ZipFile) -> ExtractedData:
        extracts: List[ExtractedData] = []
        filenames = [info.filename for info in z.infolist() if not info.is_dir()]
        file_count = len(filenames)
        logger.info(f"Total files in zip: {file_count}")

        for i, filename in enumerate(filenames):
            logger.info(f"Extracting: {filename}")

            if i % 5 == 0:
                self.feed_task_result.update_progress(round(50 + (20 * i / file_count)))

            if filename.endswith(".xml"):
                with z.open(filename, "r") as f:
                    file_obj = File(f, name=filename)
                    extracted = self.feed_parser.extractor.extract(file_obj)
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
            stop_count=len(
                concat_and_dedupe((extract.stop_points for extract in extracts))
            ),
        )
