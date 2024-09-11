from transit_odp.common.loggers import get_dataset_adapter_from_revision


class TransmodelDataLoader:
    def __init__(self, file_hash):
        self.file_hash = file_hash

    def load(self, live_revision_id):
        adapter = get_dataset_adapter_from_revision(logger, revision)
        adapter.info("Loading TransXChange queryset.")

        adapter.info("Loading services.")
        services_df = self.services_from_db_to_df(live_revision_id)
        adapter.info("Finished loading services.")

        adapter.info("Loading service patterns.")
        service_patterns = self.service_patterns_db_to_df(services, revision)
        adapter.info("Finished loading service patterns.")

    def services_from_db_to_df(revision_id):
        return pd.Dataframe.from_records(
            Service.objects.filter(revision_id=revision_id)
        )

    def service_patterns_db_to_df(revision_id):
        columns = ["revision", "service_pattern_id", "geom", "line_name", "description"]
        return pd.DataFrame.from_records(ServicePattern.filter(revision_id=revision_id))
