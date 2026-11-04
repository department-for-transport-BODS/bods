from django.views.decorators.http import require_GET

from transit_odp.fares.views.requires_attention import FaresRequiresAttentionView
from transit_odp.publish.views.requires_attention_api import (
    requires_attention_json_response,
)


def _fares_export_route(context, org_id):
    # The fares template always links to the timetables compliance report.
    return f"/org/{org_id}/dataset/timetable/compliance-report/"


@require_GET
def get_fares_requires_attention_api(request, pk1):
    return requires_attention_json_response(
        request, pk1, FaresRequiresAttentionView, _fares_export_route
    )
