"""JSON APIs backing the Next.js line detail pages.

Publish host: mirrors ``LineMetadataRevisionView`` (``revision-line-detail``).
Data host: mirrors browse ``LineMetadataDetailView`` (``feed-line-detail``).

Next.js owns the feature flags for these pages, so the timetable visualiser is
only built when the caller asks for it with ``includeTimetable=true``.
"""

import re
from datetime import datetime
from typing import Optional

import pandas as pd
from django.http import JsonResponse
from django.utils import formats
from django.views.decorators.http import require_GET

from transit_odp.browse.timetable_visualiser import TimetableVisualiser
from transit_odp.browse.views.timetable_views import LineMetadataDetailView
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.models.data import DatasetRevision
from transit_odp.publish.views.utils import (
    get_current_files,
    get_service_type,
    get_valid_files,
)
from transit_odp.timetables.views.api import _get_request_context
from transit_odp.timetables.views.review import LineMetadataRevisionView

DATASET_NOT_FOUND_ERROR = "Dataset not found"
REVISION_NOT_FOUND_ERROR = "Revision not found"
DIRECTIONS = ("outbound", "inbound")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _render(value) -> str:
    return str(value)


def _localize_date(value) -> Optional[str]:
    return formats.localize(value) if value else None


def _serialize_files(files) -> list:
    return [
        {
            "filename": file["filename"],
            "startDate": _localize_date(file["start_date"]),
            "endDate": _localize_date(file["end_date"]),
        }
        for file in files
    ]


def _serialize_booking(service_type: str, booking_arrangements_info) -> dict:
    if service_type not in ("Flexible", "Flexible/Standard"):
        return {"bookingArrangements": None, "bookingMethods": None}
    if not booking_arrangements_info:
        return {"bookingArrangements": None, "bookingMethods": None}

    description, email, phone, web = booking_arrangements_info[0]
    # The Django template gates each method on a different index from the one it
    # prints (Email shows index 0 when index 2 is set, URL shows index 2 when
    # index 0 is set). Reproduced here so both frontends read the same.
    methods = (email, phone, web)
    return {
        "bookingArrangements": description or None,
        "bookingMethods": {
            "phone": _render(methods[1]) if methods[1] else None,
            "email": _render(methods[0]) if methods[2] else None,
            "url": _render(methods[2]) if methods[0] else None,
        },
    }


def _target_date(request) -> str:
    date = request.GET.get("date", datetime.now().strftime("%Y-%m-%d"))
    if DATE_PATTERN.match(date) is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return date


def _serialize_observation(observation) -> Optional[dict]:
    if not isinstance(observation, dict) or not observation.get("title"):
        return None
    return {
        "title": observation.get("title", ""),
        "text": observation.get("text", ""),
        "resolve": observation.get("resolve", ""),
    }


def _cell_observations(stop_observations, journey_id) -> list:
    if not stop_observations:
        return []
    observations = []
    for by_journey in stop_observations.values():
        for observation in by_journey.get(journey_id) or []:
            serialized = _serialize_observation(observation)
            if serialized:
                observations.append(serialized)
    return observations


def _serialize_direction(direction: str, details: dict, bound: dict) -> dict:
    df: pd.DataFrame = bound["df_timetable"]
    stops = details.get("stops") or {}
    observations = details.get("observations") or {}
    columns = [str(column) for column in df.columns]

    rows = []
    for position, row_index in enumerate(df.index):
        stop_name = _render(df.iat[position, 0])
        stop_key = f"{stop_name}_{row_index}"
        stop = stops.get(stop_key) or {}
        cells = []
        for column_position in range(1, len(columns)):
            cell = df.iat[position, column_position]
            journey_id = cell.get("journey_id")
            cells.append(
                {
                    "departureTime": _render(cell.get("departure_time", "")),
                    "journeyId": int(journey_id) if journey_id is not None else None,
                    "observations": _cell_observations(
                        observations.get(stop_key), journey_id
                    ),
                }
            )
        rows.append(
            {
                "index": int(row_index),
                "stop": {
                    "name": stop_name,
                    "atcoCode": _render(stop["atco_code"]) if stop else "",
                    "street": _render(stop["street"]) if stop else "",
                    "indicator": _render(stop["indicator"]) if stop else "",
                    "stopType": _render(stop["stop_type"]) if stop else "",
                    "observation": _serialize_observation(stop.get("observation")),
                },
                "cells": cells,
            }
        )

    description = details.get("description")
    return {
        "direction": direction,
        "journeyName": f"{direction.capitalize()} - {description}"
        if description
        else "",
        "isEmpty": df.empty,
        "totalPage": int(bound["total_page"]),
        "currPage": int(bound["curr_page"]),
        "showAll": bool(bound["show_all"]),
        "totalRowCount": int(bound["total_row_count"]),
        "pageParam": f"{direction}Page",
        "showAllParam": f"showAll{direction.capitalize()}",
        "columns": [
            {
                "name": column,
                "observation": _serialize_observation(observations.get(column))
                if index
                else None,
            }
            for index, column in enumerate(columns)
        ],
        "rows": rows,
    }


def _serialize_timetable(
    request, revision_id: int, service_code: str, line: str, public_use: bool
) -> Optional[dict]:
    if request.GET.get("includeTimetable", "false").lower() != "true":
        return None

    date = _target_date(request)
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    visualiser_args = [revision_id, service_code, line, target_date]
    if public_use:
        visualiser_args.append(True)
    timetable = TimetableVisualiser(*visualiser_args).get_timetable_visualiser()

    pager = LineMetadataRevisionView(request=request)
    directions = []
    for direction in DIRECTIONS:
        details = timetable[direction]
        bound = pager.get_direction_timetable(details["df_timetable"], direction)
        directions.append(_serialize_direction(direction, details, bound))

    return {
        "currDate": date,
        "isTimetableInfoAvailable": any(not d["isEmpty"] for d in directions),
        "directions": directions,
    }


@require_GET
def get_timetables_line_detail_api(request, pk1, pk):
    """Publish ``revision-line-detail`` page data."""
    _, organisation, _, error_response = _get_request_context(request, pk1)
    if error_response is not None:
        return error_response

    revision = (
        DatasetRevision.objects.select_related("dataset")
        .filter(
            id=request.GET.get("revision_id") or None,
            dataset_id=pk,
            dataset__organisation_id=organisation.id,
            dataset__dataset_type=TimetableType,
        )
        .first()
    )
    if revision is None:
        return JsonResponse({"error": REVISION_NOT_FOUND_ERROR}, status=404)

    line = request.GET.get("line")
    service_code = request.GET.get("service")
    service_type = get_service_type(revision.id, service_code, line)
    current_valid_files = get_current_files(revision.id, service_code, line)
    booking_info = None
    if service_type in ("Flexible", "Flexible/Standard"):
        booking_info = get_valid_files(
            revision.id, current_valid_files, service_code, line
        )

    return JsonResponse(
        {
            "orgId": organisation.id,
            "datasetId": revision.dataset_id,
            "revisionId": revision.id,
            "feedName": revision.name,
            "lineName": line,
            "serviceCode": service_code,
            "serviceType": service_type,
            "currentValidFiles": _serialize_files(current_valid_files),
            **_serialize_booking(service_type, booking_info),
            "timetable": _serialize_timetable(
                request, revision.id, service_code, line, public_use=False
            ),
        }
    )


@require_GET
def get_browse_timetable_line_detail_api(request, pk):
    """Data ``feed-line-detail`` page data. Public, like the Django page."""
    detail_view = LineMetadataDetailView(request=request)
    dataset = detail_view.get_queryset().filter(id=pk).first()
    if dataset is None:
        return JsonResponse({"error": DATASET_NOT_FOUND_ERROR}, status=404)

    line = request.GET.get("line")
    service_code = request.GET.get("service")
    live_revision = dataset.live_revision
    payload = {
        "datasetId": dataset.id,
        "datasetName": dataset.name,
        "revisionId": live_revision.id if live_revision else None,
        "lineName": line,
        "serviceCode": service_code,
        "serviceType": "N/A",
        "currentValidFiles": [],
        "bookingArrangements": None,
        "bookingMethods": None,
        "timetable": None,
    }
    if live_revision is None:
        return JsonResponse(payload)

    current_valid_files = detail_view.get_current_files(
        live_revision.id, service_code, line
    )
    service_type = detail_view.get_service_type(live_revision.id, service_code, line)
    booking_info = None
    if service_type in ("Flexible", "Flexible/Standard"):
        booking_info = detail_view.get_valid_files(
            live_revision.id, current_valid_files, service_code, line
        )

    payload.update(
        {
            "serviceType": service_type,
            "currentValidFiles": _serialize_files(current_valid_files),
            **_serialize_booking(service_type, booking_info),
            "timetable": _serialize_timetable(
                request, live_revision.id, service_code, line, public_use=True
            ),
        }
    )
    return JsonResponse(payload)
