import pandas as pd
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.organisation.models import DatasetRevision
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.pipelines.pipelines.dataset_etl.feed_parser import FeedParser


class Command(BaseCommand):
    help = "Runs profiling"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        filepath = None  # Change Me
        filename = None  # Change Me

        with transaction.atomic():
            revision = DatasetRevisionFactory.create(
                upload_file__from_path=filepath,
                upload_file__filename=filename,
                status="pending",
            )

            # This adds an extra query which we probably do not want
            instance = (
                DatasetRevision.objects.select_related("dataset__organisation")
                .filter(id=revision.id)
                .first()
            )

            # Add task_id and feed_id to organisation_feedtaskresult
            feed_task_result = DatasetETLTaskResult(revision=instance, progress=0)
            feed_task_result.save()

            # FeedParser performs the metadata extraction
            parser = FeedParser(instance, None, feed_task_result)
            parser.index_feed()

        df = pd.DataFrame(connection.queries)
        print(df.head(20))
        print(f"Number of queries {df.shape[0]}")

        df.to_csv("connection_queries.csv", index=False)
