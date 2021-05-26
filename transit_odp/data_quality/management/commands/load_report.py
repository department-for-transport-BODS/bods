import argparse

from django.core.files import File
from django.core.management.base import BaseCommand

from transit_odp.data_quality.models import DataQualityReport
from transit_odp.data_quality.tasks import run_dqs_report_etl_pipeline
from transit_odp.organisation.models import DatasetRevision


class Command(BaseCommand):
    help = "Loads the report"

    def add_arguments(self, parser):
        parser.add_argument(
            "revision_id",
            type=int,
            help="The id of the DatasetRevision to attach the report",
            choices=list(DatasetRevision.objects.values_list("id", flat=True)),
        )
        parser.add_argument(
            "report",
            type=argparse.FileType("r"),
            help="The JSON report",
        )

    def handle(self, *args, **options):
        revision_id = options["revision_id"]
        report_file = options["report"]

        revision = DatasetRevision.objects.get(id=revision_id)

        report, created = DataQualityReport.objects.update_or_create(
            revision=revision, defaults={"file": File(report_file)}
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'{"Created" if created else "Updated"} report: {report}'
            )
        )

        self.stdout.write(self.style.SUCCESS("Running ETL task"))
        run_dqs_report_etl_pipeline(report.id)
