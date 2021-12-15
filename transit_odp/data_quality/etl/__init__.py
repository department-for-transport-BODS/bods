from dataclasses import dataclass
from logging import getLogger
from typing import List

from django.db.models.query_utils import Q

from transit_odp.common.loggers import get_dataset_adapter_from_revision
from transit_odp.data_quality.dataclasses import Report
from transit_odp.data_quality.etl.warnings import (
    FastTimingETL,
    JourneyPartialTimingOverlapETL,
    LineExpiredETL,
    LineMissingBlockIDETL,
    TimingFirstETL,
    TimingLastETL,
    TimingMissingPointETL,
    TimingMultipleETL,
)
from transit_odp.data_quality.models.report import (
    DataQualityReport,
    DataQualityReportSummary,
)
from transit_odp.data_quality.models.warnings import (
    WARNING_MODELS,
    IncorrectNOCWarning,
    JourneyStopInappropriateWarning,
    StopMissingNaptanWarning,
)
from transit_odp.timetables.transxchange import TransXChangeDatasetParser

logger = getLogger(__name__)


@dataclass
class TransXChangeExtract:
    nocs: List[str]
    transxchange_versions: List[str]


class TransXChangeDQPipeline:
    def __init__(self, model: DataQualityReport):
        self._model_report: DataQualityReport = model
        self._revision = model.revision
        self._extract: TransXChangeExtract = None
        self._parser: TransXChangeDatasetParser = None
        self._report: Report = None

    @property
    def report_id(self) -> int:
        return self._model_report.id

    @property
    def report(self) -> Report:
        if self._report:
            return self._report

        self._report = Report(self.report_file)
        return self._report

    @property
    def organistion_nocs(self) -> List[str]:
        organistion = self._model_report.revision.dataset.organisation
        nocs = organistion.nocs.values_list("noc", flat=True).distinct()
        return nocs

    @property
    def transxchange_file(self):
        self._model_report.revision.upload_file.seek(0)
        return self._model_report.revision.upload_file

    @property
    def report_file(self):
        self._model_report.file.seek(0)
        return self._model_report.file

    @property
    def parser(self) -> TransXChangeDatasetParser:
        self._parser = TransXChangeDatasetParser(self.transxchange_file)
        return self._parser

    def create_incorrect_nocs_warning(self) -> None:
        extract: TransXChangeExtract = self.extract()
        nocs = [noc for noc in set(extract.nocs) if noc not in self.organistion_nocs]
        warnings = [
            IncorrectNOCWarning(report_id=self.report_id, noc=noc) for noc in nocs
        ]
        if warnings:
            IncorrectNOCWarning.objects.bulk_create(warnings, ignore_conflicts=True)

    def create_journey_conflict_warning(self) -> None:
        warnings = self.report.filter_by_warning_type("journey-partial-timing-overlap")
        pipeline = JourneyPartialTimingOverlapETL(self.report_id, warnings)
        pipeline.load()

    def create_line_expired_warning(self) -> None:
        warnings = self.report.filter_by_warning_type("line-expired")
        pipeline = LineExpiredETL(self.report_id, warnings)
        pipeline.load()

    def create_line_missing_block_id_warnings(self) -> None:
        warnings = self.report.filter_by_warning_type("line-missing-block-id")
        pipeline = LineMissingBlockIDETL(self.report_id, warnings)
        pipeline.load()

    def create_timing_first_warnings(self) -> None:
        warnings = self.report.filter_by_warning_type("timing-first")
        pipeline = TimingFirstETL(self.report_id, warnings)
        pipeline.load()

    def create_timing_last_warnings(self) -> None:
        warnings = self.report.filter_by_warning_type("timing-last")
        pipeline = TimingLastETL(self.report_id, warnings)
        pipeline.load()

    def create_timing_multiple_warnings(self) -> None:
        warnings = self.report.filter_by_warning_type("timing-multiple")
        pipeline = TimingMultipleETL(self.report_id, warnings)
        pipeline.load()

    def create_timing_missing_point_15_warnings(self) -> None:
        warnings = self.report.filter_by_warning_type("timing-missing-point-15")
        pipeline = TimingMissingPointETL(self.report_id, warnings)
        pipeline.load()

    def create_fast_timing_warnings(self) -> None:
        warnings = self.report.filter_by_warning_type("timing-fast")
        pipeline = FastTimingETL(self.report_id, warnings)
        pipeline.load()

    def extract(self) -> TransXChangeExtract:
        if self._extract is not None:
            return self._extract

        nocs = self.parser.get_nocs()
        versions = self.parser.get_transxchange_versions()
        self._extract = TransXChangeExtract(nocs=nocs, transxchange_versions=versions)
        return self._extract

    def load_warnings(self) -> None:
        adapter = get_dataset_adapter_from_revision(logger, self._revision)
        adapter.info("Creating IncorrectNOCWarning.")
        self.create_incorrect_nocs_warning()
        adapter.info("Creating JourneyConflictWarning.")
        self.create_journey_conflict_warning()
        adapter.info("Creating LineExpiredWarning.")
        self.create_line_expired_warning()
        adapter.info("Creating LineMissingBlockIDWarning.")
        self.create_line_missing_block_id_warnings()
        adapter.info("Creating TimingFirstWarning.")
        self.create_timing_first_warnings()
        adapter.info("Creating TimingLastWarning.")
        self.create_timing_last_warnings()
        adapter.info("Creating TimingMultipleWarning.")
        self.create_timing_multiple_warnings()
        adapter.info("Creating TimingMissingPointWarning.")
        self.create_timing_missing_point_15_warnings()
        adapter.info("Creating FastTimingWarning.")
        self.create_fast_timing_warnings()

    def load(self) -> None:
        self.load_warnings()
        self.load_summary()

    def load_summary(self) -> DataQualityReportSummary:
        """
        Aggregates the total number of warnings loaded and saves the data to
        DataQualityReportSummary.
        """
        adapter = get_dataset_adapter_from_revision(logger, self._revision)
        adapter.info("Generating report summary.")
        self._model_report.refresh_from_db()

        # For certain warnings we can't be certain that the stop has a
        # service pattern. These warnings aren't shown to the user, so don't include
        # them in the count
        maybe_null_service_pattern = [
            StopMissingNaptanWarning,
            JourneyStopInappropriateWarning,
        ]

        null_service_pattern = Q(stop__service_patterns__isnull=True)
        counts = {
            model.__name__: model.objects.filter(report=self._model_report).count()
            if model not in maybe_null_service_pattern
            else model.objects.filter(report=self._model_report)
            .exclude(null_service_pattern)
            .count()
            for model in WARNING_MODELS
        }

        summary, created = DataQualityReportSummary.objects.update_or_create(
            report=self._model_report, defaults={"data": counts}
        )

    def run(self):
        adapter = get_dataset_adapter_from_revision(logger, self._revision)
        adapter.info("Extracting data from TXC file.")
        self.extract()
        self.load()
