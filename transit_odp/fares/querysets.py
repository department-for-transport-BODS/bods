from transit_odp.organisation.querysets import DatasetQuerySet
from django.db import models

class FaresDatasetQuerySet(DatasetQuerySet):
    pass


class FaresNetexFileAttributesQuerySet(models.QuerySet):
    def get_active_txc_files(self):
        return (
            self.get_active_live_revisions()
            .add_bods_compliant()
            .add_dq_score()
            .add_revision_details()
            .add_organisation_name()
            .add_string_lines()
            .order_by(
                "service_code", "-revision__dataset_id", "operating_period_start_date"
            )
            .distinct("service_code")
        )
    