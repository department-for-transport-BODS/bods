import logging

from django.db.models import Q, F, CharField, FilteredRelation, Value, DateField, Case, When
from django.db.models.functions import Coalesce
from django.db import connection

from transit_odp.transmodel.models import Service, ServicedOrganisationVehicleJourney, OperatingDatesExceptions, NonOperatingDatesExceptions
from transit_odp.timetables.utils import get_dataframe_from_queryset
from django.db import models


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TimetableVisualiser:
    def get_timetable_visualiser(self, revision_id, service_code, line_name, target_date):
        day_of_week = target_date.strftime('%A')
        queryset_all_vehicle_journeys = Service.objects.filter(
                revision_id=revision_id,
                service_code=service_code,
                service_patterns__line_name=line_name,
                service_patterns__service_pattern_stops__vehicle_journey__id=F("service_patterns__service_pattern_vehicle_journey__id")
                    ).annotate(
                service_code_s=F("service_code"),
                revision_id_s=F("revision_id"),
                service_name_s=F("name"),
                start_date_s=F("start_date"),
                end_date_s=F("end_date"),
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
                day_of_week=F('service_patterns__service_pattern_vehicle_journey__operating_profiles__day_of_week'),
                vehicle_journey_id=F("service_patterns__service_pattern_vehicle_journey__id"),
            ).values(
            'service_code',
            'revision_id',
            'name',
            'start_date',
            'end_date',
            'origin',
            'destination',
            'journey_description',
            'line_name',
            'stop_sequence',
            'departure_time',
            'is_timing_point',
            'common_name',
            'direction',
            'vehicle_journey_code',
            'line_ref',
            'departure_day_shift',
            'day_of_week',
            'vehicle_journey_id',
        )
        
        # Another queryset for txfileattributes - TBD

        queryset_serviced_orgs = ServicedOrganisationVehicleJourney.objects.select_related(
            'serviced_organisation',
        ).prefetch_related(
            'serviced_organisation__serviced_organisations_working_days'
        ).filter(
            serviced_organisation__isnull=False,
            serviced_organisation__serviced_organisations_working_days__isnull=False
        ).annotate(
            serviced_org_id=F('serviced_organisation__id'),
            vehicle_journey_id_so=F('vehicle_journey_id'),
            operating_on_working_days_so=F('operating_on_working_days'),
            name=F('serviced_organisation__name'),
            organisation_code=F('serviced_organisation__organisation_code'),
            start_date=F('serviced_organisation__serviced_organisations_working_days__start_date'),
            end_date=F('serviced_organisation__serviced_organisations_working_days__end_date'),
        ).values(
            'serviced_org_id',
            'vehicle_journey_id',
            'operating_on_working_days',
            'name',
            'organisation_code',
            'start_date',
            'end_date',
        )

        queryset_vehicle_journey_op_exceptions = OperatingDatesExceptions.objects.filter(
            operating_date=target_date
        ).annotate(
        ).values('vehicle_journey_id', 'operating_date')

        queryset_vehicle_journey_nonop_exceptions = NonOperatingDatesExceptions.objects.filter(
            non_operating_date=target_date
        ).annotate(
        ).values('vehicle_journey_id', 'non_operating_date')

        df_from_queryset = get_dataframe_from_queryset(queryset_all_vehicle_journeys, queryset_serviced_orgs, 
                                                       queryset_vehicle_journey_op_exceptions, 
                                                       queryset_vehicle_journey_nonop_exceptions)

        return queryset_all_vehicle_journeys
