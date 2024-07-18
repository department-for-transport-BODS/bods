from django.db import models
from django.db.models import F, TextField, CharField, Func
from transit_odp.dqs.constants import TaskResultsStatus, Checks
from django.db.models.expressions import Value
from django.db.models.functions import (
    Concat,
    Coalesce,
    Upper,
    Substr,
    ExtractHour,
    ExtractMinute,
    LPad,
    Cast,
)


class TaskResultsQueryset(models.QuerySet):
    """
    This queryset class is to include all querysets related to the TaskResults model
    """

    def get_valid_taskresults(self, txcfileattributes: list) -> list:
        """Get valid TaskResults objects for the TxCFiles"""
        txcfileattribute_ids = [attr.id for attr in txcfileattributes]
        return self.filter(transmodel_txcfileattributes__id__in=txcfileattribute_ids)

    def get_pending_objects(self, txcfileattributes: list) -> list:
        """
        Filter for PENDING TaskResults items for the TxCFiles and annotate queue_names from Checks
        """
        include_status = TaskResultsStatus.PENDING.value
        qs = (
            self.get_valid_taskresults(txcfileattributes)
            .filter(status=include_status)
            .annotate(queue_name=F("checks__queue_name"))
        )

        return qs


class ObservationResultsQueryset(models.QuerySet):
    """
    This queryset class is to include all querysets related to the Observation Results model
    """

    def get_observations(self, report_id: int, check: Checks, revision_id: int) -> list:
        """
        Filter for observation results for the report and revision of the specific Checks
        """

        columns = ["observation", "service_code", "line_name", "message", "dqs_details"]

        qs = (
            self.filter(
                taskresults__dataquality_report_id=report_id,
                taskresults__checks__observation=check.value,
                taskresults__dataquality_report__revision_id=revision_id,
            )
            .annotate(
                observation=F("taskresults__checks__observation"),
                service_code=F(
                    "taskresults__transmodel_txcfileattributes__service_code"
                ),
                line_name=F(
                    "taskresults__transmodel_txcfileattributes__service_txcfileattributes__name"
                ),
                message=Concat(
                    F(
                        "taskresults__transmodel_txcfileattributes__service_txcfileattributes__name"
                    ),
                    F(
                        "taskresults__transmodel_txcfileattributes__service_code",
                    ),
                ),
                dqs_details=Concat(
                    F(
                        "taskresults__transmodel_txcfileattributes__national_operator_code",
                    ),
                    Value(
                        " is specified in the dataset but not assigned to your "
                        "organisation",
                        output_field=TextField(),
                    ),
                    output_field=TextField(),
                ),
            )
            .values(*columns)
        )

        return qs

    def get_observations_grouped(
        self,
        report_id: int,
        check: Checks,
        revision_id: int,
        dqs_details: str = "Message in details",
    ) -> list:
        """
        Filter for observation results for the report and revision of the specific check and ingesting the message
        """

        columns = ["service_code", "line_name", "message", "dqs_details"]

        qs = (
            self.filter(
                taskresults__dataquality_report_id=report_id,
                taskresults__checks__observation=check.value,
                taskresults__dataquality_report__revision_id=revision_id,
            )
            .annotate(
                service_code=F(
                    "taskresults__transmodel_txcfileattributes__service_code"
                ),
                line_name=F(
                    "taskresults__transmodel_txcfileattributes__service_txcfileattributes__name"
                ),
                message=Value("", output_field=TextField()),
                dqs_details=Value(dqs_details, output_field=TextField()),
            )
            .values(*columns)
            .distinct()
        )

        return qs

    def get_observations_details(
        self,
        report_id: int,
        check: Checks,
        revision_id: int,
        is_stop_type: bool = False,
    ):
        columns = ["journey_start_time", "direction", "stop_name"]

        if is_stop_type:
            columns.append("stop_type")

        qs = (
            self.filter(
                taskresults__dataquality_report_id=report_id,
                taskresults__checks__observation=check.value,
                taskresults__dataquality_report__revision_id=revision_id,
            )
            .annotate(
                # service_pattern_stop
                journey_start_time=Concat(
                    LPad(
                        Cast(
                            ExtractHour(F("vehicle_journey__start_time")),
                            output_field=CharField(),
                        ),
                        2,
                        Value("0"),
                    ),
                    Value(":"),
                    LPad(
                        Cast(
                            ExtractMinute(F("vehicle_journey__start_time")),
                            output_field=CharField(),
                        ),
                        2,
                        Value("0"),
                    ),
                ),
                direction=Concat(
                    Upper(Substr(F("vehicle_journey__direction"), 1, 1)),
                    Substr(F("vehicle_journey__direction"), 2),
                ),
                stop_name=Concat(
                    Coalesce(
                        "service_pattern_stop__naptan_stop__common_name",
                        "service_pattern_stop__txc_common_name",
                        output_field=CharField(),
                    ),
                    Value(" ("),
                    F("service_pattern_stop__naptan_stop__atco_code"),
                    Value(")"),
                ),
                stop_type=F("service_pattern_stop__naptan_stop__stop_type"),
            )
            .values(*columns)
        )

        return qs
