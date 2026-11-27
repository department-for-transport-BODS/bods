"""
JSON APIs backing the Next.js data quality report, observation and glossary pages.

These mirror the new data quality service (DQS) Django views in
``transit_odp.dqs.views`` and ``transit_odp.data_quality.views``.
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Tuple

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from waffle import flag_is_active

from transit_odp.common.utils.s3_bucket_connection import get_dqs_report_from_s3
from transit_odp.data_quality.report_summary import Summary
from transit_odp.data_quality.views.glossary import get_glossary_category_by_level
from transit_odp.dqs import constants as dqs
from transit_odp.dqs.constants import Checks, Level, Observation, ReportStatus
from transit_odp.dqs.models import ObservationResults, Report
from transit_odp.dqs.views.suppress_observation import SuppressObservationView
from transit_odp.organisation.models import ConsumerFeedback
from transit_odp.timetables.views.api import _get_request_context

DATA_QUALITY_REPORT_NOT_FOUND_ERROR = "Data quality report not found"
OBSERVATION_NOT_FOUND_ERROR = "Observation not found"
SERVICE_REQUIRED_ERROR = "Service and line are required"
SUPPRESS_NOT_ALLOWED_ERROR = "This observation cannot be suppressed"
PAGE_SIZE = 10

FIRST_STOP = "First stop"
LAST_STOP = "Last stop"


@dataclass(frozen=True)
class ObservationPage:
    observation: Observation
    check: Optional[Checks]
    details: Optional[str] = None
    col_name: str = ""
    detail_subtitle: Optional[str] = None
    stop_label: str = "Stop name"
    extra_columns: Tuple[Tuple[str, str], ...] = ()
    columns: Optional[Tuple[Tuple[str, str], ...]] = None
    detail_text: dict = field(default_factory=dict)
    is_feedback: bool = False

    @property
    def has_detail(self):
        return self.detail_subtitle is not None

    @property
    def can_suppress_list(self):
        return not self.is_feedback and self.observation.level is Level.advisory

    def detail_columns(self):
        if self.columns is not None:
            return self.columns
        return (
            ("journey_start_time", "Journey start time"),
            ("direction", "Direction"),
            ("stop_name", self.stop_label),
        ) + self.extra_columns


# Keyed by the legacy report URL slug (see report_summary.URL_MAPPING)
OBSERVATION_PAGES = {
    "drop-off-only": ObservationPage(
        observation=dqs.FirstStopSetDownOnlyObservation,
        check=Checks.FirstStopIsSetDown,
        details=(
            "There is at least one journey where the first stop is designated as "
            "set down only"
        ),
        detail_subtitle=(
            "has at least one journey where the first stop is designated as "
            "set down only"
        ),
        stop_label=FIRST_STOP,
    ),
    "pick-up-only": ObservationPage(
        observation=dqs.LastStopPickUpOnlyObservation,
        check=Checks.LastStopIsPickUpOnly,
        details=(
            "There is at least one journey where the last stop is designated as "
            "pick up only"
        ),
        detail_subtitle=(
            "has at least one journey where the last stop is designated as "
            "pick up only"
        ),
        stop_label=LAST_STOP,
    ),
    "first-stop-not-timing-point": ObservationPage(
        observation=dqs.FirstStopNotTimingPointObservation,
        check=Checks.FirstStopIsNotATimingPoint,
        details=(
            "There is at least one journey where the first stop is not a timing point"
        ),
        detail_subtitle=(
            "has at least one journey where the first stop is not a timing point"
        ),
        stop_label=FIRST_STOP,
    ),
    "last-stop-not-timing-point": ObservationPage(
        observation=dqs.LastStopNotTimingPointObservation,
        check=Checks.LastStopIsNotATimingPoint,
        details=(
            "There is at least one journey where the last stop is not a timing point"
        ),
        detail_subtitle=(
            "has at least one journey where the last stop is not a timing point"
        ),
        stop_label=LAST_STOP,
    ),
    "stop-not-in-naptan": ObservationPage(
        observation=dqs.StopNotInNaptanObservation,
        check=Checks.StopNotFoundInNaptan,
        details="There is at least one stop that is not registered with NaPTAN",
        detail_subtitle=(
            "has at least one journey with a stop that is not found in NaPTAN"
        ),
    ),
    "incorrect-stop-type": ObservationPage(
        observation=dqs.IncorrectStopTypeObservation,
        check=Checks.IncorrectStopType,
        details="There is at least one stop with an incorrect stop type",
        detail_subtitle=(
            "has at least one journey with a stop of the incorrect type in NaPTAN."
        ),
        extra_columns=(("stop_type", "Stop type"),),
    ),
    "missing-journey-code": ObservationPage(
        observation=dqs.MissingJourneyCodeObservation,
        check=Checks.MissingJourneyCode,
        details="There is at least one journey that is missing a journey code ",
        detail_subtitle="has at least one journey with a missing journey code",
        stop_label=FIRST_STOP,
    ),
    "duplicate-journey-code": ObservationPage(
        observation=dqs.DuplicateJourneyCodeObservation,
        check=Checks.DuplicateJourneyCode,
        details="There is at least one journey that has a duplicate journey code ",
        detail_subtitle="has at least one journey with a duplicate journey code",
        stop_label=FIRST_STOP,
        extra_columns=(("journey_code", "Journey code"),),
    ),
    "no-timing-point-more-than-15-minutes": ObservationPage(
        observation=dqs.NoTimingPointMoreThan15MinsObservation,
        check=Checks.NoTimingPointMoreThan15Minutes,
        details=(
            "There is at least one timing point more than 15 minutes away from the "
            "previous timing point"
        ),
        detail_subtitle=(
            "has at least one journey with a pair of timings of more than 15 minutes"
        ),
        stop_label="Timing point",
    ),
    "missing-bus-working-number": ObservationPage(
        observation=dqs.MissingBusWorkingNumberObservation,
        check=Checks.MissingBusWorkingNumber,
        details="There is at least one journey that is missing a bus working number",
        detail_subtitle="has at least one journey with a missing bus working number",
        stop_label=FIRST_STOP,
    ),
    "serviced-organisation-out-of-date": ObservationPage(
        observation=dqs.ServicedOrganisationOutOfDateObservation,
        check=Checks.ServicedOrganisationOutOfDate,
        details="There is at least one serviced organisation that is out of date",
        detail_subtitle=(
            "has at least one journey linked to a serviced organisation that is "
            "out of date"
        ),
        columns=(
            ("serviced_organisation", "Serviced organisation"),
            ("serviced_organisation_code", "Serviced organisation code"),
            ("last_working_day", "Last working day"),
        ),
        detail_text={
            "subtitleDescription": "Which serviced organisations have been affected?",
            "totalDescription": "Total serviced organisations",
            "listText": "serviced organisations",
        },
    ),
    "incorrect-noc": ObservationPage(
        observation=dqs.IncorrectNocObservation,
        check=Checks.IncorrectNoc,
        col_name="noc",
    ),
    "incorrect-licence-number": ObservationPage(
        observation=dqs.IncorrectLicenceNumberObservation,
        check=Checks.IncorrectLicenceNumber,
        col_name="lic",
    ),
    "cancelled-service-appearing-active": ObservationPage(
        observation=dqs.CancelledServiceAppearingActiveObservation,
        check=Checks.CancelledServiceAppearingActive,
        col_name="cancelled_service",
    ),
    "feedback": ObservationPage(
        observation=dqs.ConsumerFeedbackObservation,
        check=None,
        details="There is at least one consumer feedback received",
        detail_subtitle="has at least one feedback message to address.",
        columns=(
            ("journey_start_time", "Journey start time"),
            ("direction", "Direction"),
            ("stop_name", "Stop name"),
            ("message", "Message"),
        ),
        detail_text={
            "subtitleDescription": "How many feedbacks have been raised by consumers?",
            "totalDescription": "Consumer feedback observations",
            "totalDescriptionShort": "detected",
            "listText": "consumer feedback",
        },
        is_feedback=True,
    ),
}

DEFAULT_DETAIL_TEXT = {
    "subtitleDescription": "Which journeys have been affected?",
    "totalDescription": "Total vehicle journeys",
    "totalDescriptionShort": "affected",
    "listText": "vehicle journeys for this service",
}


def _not_found(message):
    return JsonResponse({"error": message}, status=404)


def _get_report(request, pk1, pk, report_id):
    _, organisation, _, error_response = _get_request_context(request, pk1)
    if error_response is not None:
        return None, error_response

    report = (
        Report.objects.select_related("revision")
        .filter(
            id=report_id,
            revision__dataset_id=pk,
            revision__dataset__organisation_id=organisation.id,
        )
        .first()
    )
    if report is None:
        return None, _not_found(DATA_QUALITY_REPORT_NOT_FOUND_ERROR)
    return report, None


def _get_observation_page(slug):
    return OBSERVATION_PAGES.get(slug)


def _serialise_observation(observation: Observation):
    extra_info = observation.extra_info or {}
    return {
        "title": observation.title,
        "level": observation.level.value,
        "text": observation.text,
        "impacts": observation.impacts,
        "resolve": observation.resolve,
        "preamble": observation.preamble,
        "isActive": observation.is_active,
        "extraInfo": [
            {"code": code, "description": description}
            for code, description in extra_info.items()
        ],
    }


def _paginate(request, rows):
    page = Paginator(rows, PAGE_SIZE).get_page(request.GET.get("page"))
    return page, {
        "page": page.number,
        "totalPages": page.paginator.num_pages,
        "totalCount": page.paginator.count,
    }


def _serialise_data_quality_level(level, level_data):
    categories = []
    for category, df in level_data.get("df", {}).items():
        observations = []
        for _, row in df.iterrows():
            slug = row.get("url")
            observations.append(
                {
                    "observation": row["observation"],
                    "slug": slug if slug in OBSERVATION_PAGES else None,
                    "count": int(
                        row["number_of_services_affected"]
                        - row["number_of_suppressed_observation"]
                    ),
                    "suppressedCount": int(row["number_of_suppressed_observation"]),
                }
            )
        categories.append(
            {
                "category": category,
                "count": sum(item["count"] for item in observations),
                "suppressedCount": sum(
                    item["suppressedCount"] for item in observations
                ),
                "observations": observations,
            }
        )

    return {
        "level": level,
        "count": int(level_data.get("count", 0)),
        "intro": level_data.get("intro", ""),
        "categories": categories,
    }


@require_GET
def get_timetables_data_quality_report_api(request, pk1, pk):
    _, _, revision, error_response = _get_request_context(request, pk1, pk)
    if error_response is not None:
        return error_response

    report = (
        Report.objects.filter(
            revision_id=revision.id, status=ReportStatus.REPORT_GENERATED.value
        )
        .order_by("-created")
        .first()
    )
    if report is None:
        return _not_found(DATA_QUALITY_REPORT_NOT_FOUND_ERROR)

    summary = Summary.get_report(report.id, revision.id)
    levels = [
        _serialise_data_quality_level(level, level_data)
        for level, level_data in summary.data.items()
    ]
    level_counts = {level["level"]: level["count"] for level in levels}

    return JsonResponse(
        {
            "reportId": report.id,
            "title": revision.name,
            "busServicesAffected": int(summary.bus_services_affected),
            "hasCriticalIssues": any(
                level_counts.get(level, 0) > 0 for level in ("Critical", "Feedback")
            ),
            "levels": levels,
        }
    )


@require_GET
def download_timetables_data_quality_report_csv_api(request, pk1, pk, report_id):
    report, error_response = _get_report(request, pk1, pk, report_id)
    if error_response is not None:
        return error_response
    return get_dqs_report_from_s3(report.file_name)


def _get_list_rows(page_config: ObservationPage, report: Report, org_id):
    is_published = report.revision.is_published
    if page_config.is_feedback:
        feedbacks = ConsumerFeedback.objects.get_feedbacks(
            report.id,
            report.revision_id,
            is_published,
            page_config.details,
            True,
            org_id,
        )
        rows, seen = [], set()
        for feedback in feedbacks:
            key = (feedback.get("service_code"), feedback.get("line_name"))
            if all(key) and key not in seen:
                seen.add(key)
                rows.append(feedback)
        return rows

    return ObservationResults.objects.get_observations(
        report.id,
        page_config.check,
        report.revision_id,
        is_published,
        page_config.details,
        page_config.has_detail,
        page_config.col_name,
        org_id,
        True,
        page_config.can_suppress_list,
    )


@require_GET
def get_timetables_data_quality_observation_api(request, pk1, pk, report_id, slug):
    report, error_response = _get_report(request, pk1, pk, report_id)
    if error_response is not None:
        return error_response
    page_config = _get_observation_page(slug)
    if page_config is None:
        return _not_found(OBSERVATION_NOT_FOUND_ERROR)

    page, pagination = _paginate(
        request,
        _get_list_rows(page_config, report, report.revision.dataset.organisation_id),
    )
    return JsonResponse(
        {
            "reportId": report.id,
            "revisionId": report.revision_id,
            "isPublished": report.revision.is_published,
            "observation": _serialise_observation(page_config.observation),
            "hasDetail": page_config.has_detail,
            "canSuppress": page_config.can_suppress_list,
            **pagination,
            "rows": [
                {
                    "serviceCode": row["service_code"],
                    "lineName": row["line_name"],
                    "details": row["dqs_details"],
                    "isSuppressed": bool(row.get("is_suppressed")),
                }
                for row in page.object_list
            ],
        }
    )


@require_GET
def get_timetables_data_quality_observation_detail_api(
    request, pk1, pk, report_id, slug
):
    report, error_response = _get_report(request, pk1, pk, report_id)
    if error_response is not None:
        return error_response
    page_config = _get_observation_page(slug)
    if page_config is None or not page_config.has_detail:
        return _not_found(OBSERVATION_NOT_FOUND_ERROR)

    service = request.GET.get("service")
    line = request.GET.get("line")
    if not service or not line:
        return JsonResponse({"error": SERVICE_REQUIRED_ERROR}, status=400)

    if page_config.is_feedback:
        rows = ConsumerFeedback.objects.get_feedback_details(
            report.revision_id, service, line, True, True
        )
    else:
        rows = ObservationResults.objects.get_observations_details(
            report.id, page_config.check, report.revision_id, service, line
        )

    columns = page_config.detail_columns()
    page, pagination = _paginate(request, rows)
    return JsonResponse(
        {
            "reportId": report.id,
            "title": page_config.observation.title,
            "subtitle": f"Service {line} {page_config.detail_subtitle}",
            **DEFAULT_DETAIL_TEXT,
            **page_config.detail_text,
            "isFeedback": page_config.is_feedback,
            "canSuppress": page_config.is_feedback,
            "columns": [{"key": key, "label": label} for key, label in columns],
            **pagination,
            "rows": [
                {
                    "rowId": row.get("row_id"),
                    "isSuppressed": bool(row.get("is_suppressed")),
                    "feedback": row.get("feedback") or "",
                    "values": {
                        key: "" if row.get(key) is None else str(row.get(key))
                        for key, _ in columns
                    },
                }
                for row in page.object_list
            ],
        }
    )


def _json_body(request):
    try:
        body = json.loads(request.body or "{}")
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


@require_POST
def suppress_timetables_data_quality_observation_api(request, pk1, pk, report_id, slug):
    report, error_response = _get_report(request, pk1, pk, report_id)
    if error_response is not None:
        return error_response
    page_config = _get_observation_page(slug)
    if page_config is None:
        return _not_found(OBSERVATION_NOT_FOUND_ERROR)
    if not (page_config.is_feedback or page_config.can_suppress_list):
        return JsonResponse({"error": SUPPRESS_NOT_ALLOWED_ERROR}, status=400)

    body = _json_body(request)
    service_code = body.get("serviceCode") or None
    line_name = body.get("lineName") or None
    is_suppressed = bool(body.get("isSuppressed", False))

    suppressor = SuppressObservationView()
    if page_config.is_feedback:
        updated = suppressor.update_observation_feedback(
            report.revision.dataset.organisation_id,
            report.revision_id,
            service_code,
            line_name,
            is_suppressed,
            body.get("rowId") or None,
        )
    else:
        updated = suppressor.update_observation_results(
            report.id,
            page_config.check.value,
            service_code,
            line_name,
            is_suppressed,
        )

    return JsonResponse({"updated": updated, "isSuppressed": is_suppressed})


@require_GET
def get_data_quality_definitions_api(request):
    levels = [Level.critical, Level.advisory]
    if flag_is_active("", "is_specific_feedback"):
        levels.append(Level.feedback)

    response = []
    for level in levels:
        categories = get_glossary_category_by_level(
            dqs.OBSERVATIONS, level, show_category=level is not Level.feedback
        )
        response.append(
            {
                "level": level.value,
                "count": sum(len(category.observations) for category in categories),
                "intro": dqs.FEEDBACK_INTRO if level is Level.feedback else None,
                "categories": [
                    {
                        "type": category.type,
                        "showCategory": category.show_category_type,
                        "observations": [
                            _serialise_observation(observation)
                            for observation in category.observations
                        ],
                    }
                    for category in categories
                ],
            }
        )

    return JsonResponse({"levels": response})
