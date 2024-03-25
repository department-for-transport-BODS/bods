import logging

from django.db.models import Q, F, CharField, FilteredRelation, Value, DateField, Case, When
from django.db.models.functions import Coalesce
from django.db import connection

from transit_odp.transmodel.models import Service, ServicePattern
from transit_odp.timetables.utils import get_dataframe_from_queryset


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TimetableVisualiser:
    def get_timetable_visualiser(self, revision_id, service_code, line_name, target_date):
        day_of_week = target_date.strftime('%A')
        queryset = Service.objects.filter(
                    Q(service_patterns__service_pattern_vehicle_journey__non_operating_dates_exceptions__isnull=True) &
                (
                    Q(service_patterns__service_pattern_vehicle_journey__operating_dates_exceptions__isnull=False) |
                    Q(service_patterns__service_pattern_vehicle_journey__operating_profiles__isnull=False) |
                    Q(service_patterns__service_pattern_vehicle_journey__vehicle_journeys__serviced_organisation__serviced_organisations_working_days__isnull=False)                
                ),
                revision_id=revision_id,
                service_code=service_code,
                service_patterns__line_name=line_name
                    ).annotate(
                service_code_v=F("service_code"),
                revision_id_v=F("revision_id"),
                service_name=F("name"),
                start_date_v=F("start_date"),
                end_date_v=F("end_date"),
                other_names_v=F("other_names"),
                origin=F("service_patterns__origin"),
                destination=F("service_patterns__destination"),
                journey_description=F("service_patterns__description"),
                line_name=F("service_patterns__line_name"),
                stop_sequence=F("service_patterns__service_pattern_stops__sequence_number"),
                departure_time=F("service_patterns__service_pattern_stops__departure_time"),
                is_timing_point=F("service_patterns__service_pattern_stops__is_timing_point"),
                common_name=Coalesce(
                    "service_patterns__service_pattern_stops__naptan_stop__common_name",
                    "service_patterns__service_pattern_stops__txc_common_name",
                    output_field=CharField(),
                ),
                direction=F("service_patterns__service_pattern_vehicle_journey__direction"),
                vehicle_journey_code=F("service_patterns__service_pattern_vehicle_journey__journey_code"),
                line_ref=F("service_patterns__service_pattern_vehicle_journey__line_ref"),
                departure_day_shift=F("service_patterns__service_pattern_vehicle_journey__departure_day_shift"),
                org_name=F("service_patterns__service_pattern_vehicle_journey__vehicle_journeys__serviced_organisation__name"),
                working_start_date=F("service_patterns__service_pattern_vehicle_journey__vehicle_journeys__serviced_organisation__serviced_organisations_working_days__start_date"),
                working_end_date=F("service_patterns__service_pattern_vehicle_journey__vehicle_journeys__serviced_organisation__serviced_organisations_working_days__end_date"),
                serviced_organisation_vehicle_journey_id=F("service_patterns__service_pattern_vehicle_journey__vehicle_journeys__id"),
                serviced_organisation_id=F("service_patterns__service_pattern_vehicle_journey__vehicle_journeys__serviced_organisation__id"),
                # op_exception_operatingdate=F("service_patterns__service_pattern_vehicle_journey__operating_dates_exceptions__operating_date"),
                nonop_exception_operatingdate=F("service_patterns__service_pattern_vehicle_journey__non_operating_dates_exceptions__non_operating_date"),
                day_of_week=F("service_patterns__service_pattern_vehicle_journey__operating_profiles__day_of_week"),
                op_exception_operatingdate=Case(
                    When(
                         Q(service_patterns__service_pattern_vehicle_journey__operating_dates_exceptions__operating_date=target_date),
                         then=F('service_patterns__service_pattern_vehicle_journey__operating_dates_exceptions__operating_date')
                    ),
                     default=Value(None),
                     output_field=DateField()
                ),
                day_of_week=Case(
                When(
                    Q(service_patterns__service_pattern_vehicle_journey__operating_dates_exceptions__isnull=True) &
                    Q(service_patterns__service_pattern_vehicle_journey__operating_profiles__day_of_week='Sunday'),
                    then=F('service_patterns__service_pattern_vehicle_journey__operating_profiles__day_of_week')
                    ),
                    default=Value(''),
                    output_field=CharField()
                ),
                vehicle_journey_id=F("service_patterns__service_pattern_vehicle_journey__id"),
            )
        
        # Q(service_patterns__service_pattern_vehicle_journey__operating_dates_exceptions__operating_date=target_date)
        
        print(f"***************************** {str(queryset.query)}")
        # for query in connection.queries:
        #     print(f"***************************** {query['sql']}")
        df_from_queryset = get_dataframe_from_queryset(queryset)
        return df_from_queryset