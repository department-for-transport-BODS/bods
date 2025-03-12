import logging
from django.db.models import CharField, F
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from transit_odp.transmodel.models import Service
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UserFeedback:
    """
    User feedback for the capturing of the feedback for the specific revision id,
    service code, journey stop, journey code respectively.
    """

    def __init__(
        self,
        revision_id: str,
        service_name: str,
        line_name: str,
        stop: str,
        direction: str,
        atco_code: str,
        journey_code: str,
    ) -> None:
        """
        Intializes the properties of the object.
        """
        self._revision_id = revision_id
        self._service_name = service_name
        self._line_name = line_name
        self._stop = stop
        self._direction = direction
        self._atco_code = atco_code
        self._journey_code = journey_code

    def default(self) -> dict[str, Any]:
        """
        Return the response if unable to find the details in the DB
        """
        return {
            "revision_id": self._revision_id,
            "service_name": self._service_name,
            "line_name": self._line_name,
            "direction": self._direction,
            "stop_name": self._stop,
            "atco_code": self._atco_code,
            "start_time": None,
            "service_id": None,
            "vehicle_journey_id": None,
            "service_pattern_stop_id": None,
            "service_pattern_id": None,
        }

    def data(self, qs) -> dict[str, Any]:
        """
        Return the data after populating from the respective fields
        """
        return {
            "revision_id": self._revision_id,
            "service_name": self._service_name,
            "line_name": self._line_name,
            "direction": self._direction.capitalize() if self._direction else None,
            "stop_name": qs.common_name if self._stop else None,
            "atco_code": qs.atco_code if self._stop else None,
            "start_time": (
                qs.start_time.strftime("%H:%M") if self._journey_code else None
            ),
            "service_id": qs.id,
            "vehicle_journey_id": (
                qs.vehicle_journey_id if self._journey_code else None
            ),
            "service_pattern_stop_id": (
                qs.service_pattern_stop_id if self._stop else None
            ),
            "service_pattern_id": qs.service_pattern_id if qs.id else None,
        }

    def get_qs_service(self):
        """
        Get the query set for the specific service based on service name and line name
        """
        qs = (
            Service.objects.filter(
                revision=self._revision_id,
                service_code=self._service_name,
                service_patterns__line_name=self._line_name,
            )
            .annotate(
                line_name=F("service_patterns__line_name"),
                service_pattern_stop_id=F(
                    "service_patterns__service_pattern_stops__id"
                ),
                atco_code=F(
                    "service_patterns__service_pattern_stops__atco_code",
                ),
                common_name=Coalesce(
                    "service_patterns__service_pattern_stops__naptan_stop__common_name",
                    "service_patterns__service_pattern_stops__txc_common_name",
                    output_field=CharField(),
                ),
                service_pattern_id=F("service_patterns__id"),
            )
            .first()
        )
        return qs

    def get_qs_stop(self):
        """
        Get the query set for the specific stop name
        """

        qs = Service.objects.filter(
            revision=self._revision_id,
            service_code=self._service_name,
            service_patterns__line_name=self._line_name,
            service_patterns__service_pattern_vehicle_journey__direction=self._direction,
            service_patterns__service_pattern_stops__atco_code=self._atco_code,
        ).annotate(
            line_name=F("service_patterns__line_name"),
            service_pattern_stop_id=F("service_patterns__service_pattern_stops__id"),
            atco_code=F(
                "service_patterns__service_pattern_stops__atco_code",
            ),
            common_name=Coalesce(
                "service_patterns__service_pattern_stops__naptan_stop__common_name",
                "service_patterns__service_pattern_stops__txc_common_name",
                output_field=CharField(),
            ),
            service_pattern_id=F("service_patterns__id"),
        )

        qs = qs.filter(common_name=self._stop).first()
        return qs

    def get_qs_journey_code(self) -> QuerySet:
        """
        Get the query set for the specific journey code
        """

        journey_code = "" if self._journey_code == "-" else self._journey_code
        return (
            Service.objects.filter(
                revision=self._revision_id,
                service_code=self._service_name,
                service_patterns__line_name=self._line_name,
                service_patterns__service_pattern_vehicle_journey__journey_code=journey_code,
                service_patterns__service_pattern_vehicle_journey__direction=self._direction,
            )
            .annotate(
                direction=F(
                    "service_patterns__service_pattern_vehicle_journey__direction"
                ),
                start_time=F(
                    "service_patterns__service_pattern_vehicle_journey__start_time"
                ),
                vehicle_journey_id=F(
                    "service_patterns__service_pattern_vehicle_journey__id"
                ),
                service_pattern_id=F("service_patterns__id"),
            )
            .first()
        )
