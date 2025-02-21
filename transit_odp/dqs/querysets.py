from django.db import models
from django.db.models import F, TextField, CharField, BooleanField, Max, Func
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
from transit_odp.browse.constants import (
    REPORT_BASE_PAGE_COLUMNS,
    REPORT_DETAILS_PAGE_COLUMNS,
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

    def get_observations(
        self,
        report_id: int,
        check: Checks,
        revision_id: int,
        is_published: bool = False,
        dqs_details: str = None,
        is_details_link: bool = True,
        col_name: str = "",
        org_id: int = None,
        show_suppressed: bool = False,
        show_suppressed_button: bool = False,
    ) -> list:
        """
        Filter for observation results for the report and revision of the specific Checks
        """

        if col_name == "noc":
            col_value = F(
                "taskresults__transmodel_txcfileattributes__national_operator_code",
            )
            col_text = (
                " is specified in the dataset but not assigned to your organisation"
            )
        elif col_name == "lic":
            col_value = F(
                "taskresults__transmodel_txcfileattributes__licence_number",
            )
            col_text = (
                " is specified in the dataset but not assigned to your organisation"
            )
        elif col_name == "cancelled_service":
            col_value = F(
                "taskresults__transmodel_txcfileattributes__service_code",
            )
            col_text = (
                " is specified in the data set but is not registered with a local bus"
                " registrations authority"
            )
        else:
            col_value = Value(
                "",
                output_field=TextField(),
            )

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
                dqs_details=(
                    Concat(
                        col_value,
                        Value(
                            col_text,
                            output_field=TextField(),
                        ),
                        output_field=TextField(),
                    )
                    if not dqs_details
                    else Value(dqs_details, output_field=TextField())
                ),
                revision_id=Value(revision_id, output_field=TextField()),
                is_published=Value(is_published, output_field=BooleanField()),
                is_details_link=Value(is_details_link, output_field=BooleanField()),
                organisation_id=Value(org_id, output_field=TextField()),
                report_id=Value(report_id, output_field=TextField()),
                show_suppressed=Value(show_suppressed, output_field=BooleanField()),
                show_suppressed_button=Value(
                    show_suppressed_button, output_field=BooleanField()
                ),
                is_feedback=Value(False, output_field=BooleanField()),
            )
            .values(*REPORT_BASE_PAGE_COLUMNS)
            .distinct()
        )

        return qs

    def get_observations_details(
        self,
        report_id: int,
        check: Checks,
        revision_id: int,
        service: str,
        line: str,
    ):

        qs = (
            self.filter(
                taskresults__dataquality_report_id=report_id,
                taskresults__checks__observation=check.value,
                taskresults__dataquality_report__revision_id=revision_id,
                taskresults__transmodel_txcfileattributes__service_code=service,
                taskresults__transmodel_txcfileattributes__service_txcfileattributes__name=line,
            )
            .annotate(
                observation=F("taskresults__checks__observation"),
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
                    Coalesce(
                        F("service_pattern_stop__naptan_stop__atco_code"),
                        F("service_pattern_stop__atco_code"),
                        output_field=CharField(),
                    ),
                    Value(")"),
                ),
                stop_type=F("service_pattern_stop__naptan_stop__stop_type"),
                journey_code=F("vehicle_journey__journey_code"),
                serviced_organisation=F(
                    "serviced_organisation_vehicle_journey__serviced_organisation__name"
                ),
                serviced_organisation_code=F(
                    "serviced_organisation_vehicle_journey__serviced_organisation__organisation_code"
                ),
                last_working_day=Func(
                    Max(
                        F(
                            "serviced_organisation_vehicle_journey__serviced_organisations_vehicle_journey__end_date"
                        )
                    ),
                    Value("dd/MM/yyyy"),
                    function="TO_CHAR",  # TO_CHAR is for PostgreSQL
                    output_field=CharField(),
                ),
                is_feedback=Value(False, output_field=BooleanField()),
                message=Value(""),
                show_suppressed=Value(False, output_field=BooleanField()),
                show_suppressed_button=Value(False, output_field=BooleanField()),
                feedback=Value("", output_field=TextField()),
                row_id=Value(0),
            )
            .values(*REPORT_DETAILS_PAGE_COLUMNS)
            .distinct()
        )

        print(qs.query)

        return qs
