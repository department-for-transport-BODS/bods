import logging

from django.db.models import (
    Q,
    F,
    CharField,
)
from django.db.models.functions import Coalesce

from transit_odp.transmodel.models import (
    Service,
    ServicedOrganisationVehicleJourney,
    OperatingDatesExceptions,
    NonOperatingDatesExceptions,
)
from transit_odp.timetables.utils import (
    get_vehicle_journeys_operating_nonoperating,
    filter_df_serviced_org_operating,
    get_df_operating_vehicle_journey,
    get_df_timetable_visualiser,
)
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TimetableVisualiser:

    """
    Timetable visualiser for the capturing of the time and the stops with journey codes
    for the specific revision id, service code, line running on the target date on the
    routes.
    """

    def __init__(self, revision_id, service_code, line_name, target_date) -> None:
        """
        Intializes the properties of the class.
        """
        self._revision_id = revision_id
        self._service_code = service_code
        self._line_name = line_name
        self._target_date = target_date
        self._day_of_week = target_date.strftime("%A")

    def get_df_op_exceptions_vehicle_journey(
        self, vehicle_journey_ids: set
    ) -> pd.DataFrame:
        """
        Get the dataframe of vehicle journey which are operating on the target date
        """
        columns = ["vehicle_journey_id", "operating_date"]
        qs_vehicle_journey_op_exceptions = (
            OperatingDatesExceptions.objects.filter(
                vehicle_journey_id__in=vehicle_journey_ids
            )
            .annotate()
            .values(*columns)
        )

        return pd.DataFrame.from_records(qs_vehicle_journey_op_exceptions)

    def get_df_nonop_exceptions_vehicle_journey(
        self, vehicle_journey_ids: set
    ) -> pd.DataFrame:
        """
        Get the dataframe of vehicle journey which are not operating on the target date

        """
        columns = ["vehicle_journey_id", "non_operating_date"]
        qs_vehicle_journey_nonop_exceptions = (
            NonOperatingDatesExceptions.objects.filter(
                non_operating_date=self._target_date,
                vehicle_journey_id__in=vehicle_journey_ids,
            )
            .annotate()
            .values(*columns)
        )

        return pd.DataFrame.from_records(qs_vehicle_journey_nonop_exceptions)

    def get_df_servicedorg_vehicle_journey(
        self, vehicle_journey_ids: set
    ) -> pd.DataFrame:
        """
        Get the dataframe of vehicle journey and working days of the serviced organisation
        """
        columns = [
            "serviced_org_id",
            "vehicle_journey_id",
            "operating_on_working_days",
            "name",
            "organisation_code",
            "start_date",
            "end_date",
        ]

        qs_serviced_orgs = (
            ServicedOrganisationVehicleJourney.objects.select_related(
                "serviced_organisation",
            )
            .prefetch_related(
                "serviced_organisation__serviced_organisations_working_days"
            )
            .filter(
                serviced_organisation__isnull=False,
                serviced_organisation__serviced_organisations_working_days__isnull=False,
                vehicle_journey_id__in=vehicle_journey_ids,
            )
            .annotate(
                serviced_org_id=F("serviced_organisation__id"),
                vehicle_journey_id_so=F("vehicle_journey_id"),
                operating_on_working_days_so=F("operating_on_working_days"),
                name=F("serviced_organisation__name"),
                organisation_code=F("serviced_organisation__organisation_code"),
                start_date=F(
                    "serviced_organisation__serviced_organisations_working_days__start_date"
                ),
                end_date=F(
                    "serviced_organisation__serviced_organisations_working_days__end_date"
                ),
            )
            .values(*columns)
        )

        return pd.DataFrame.from_records(qs_serviced_orgs)

    def get_df_all_vehicle_journeys(self) -> pd.DataFrame:
        """
        Get the dataframe of vehicle journey for the service wrt service code, revision and line name
        """

        columns = [
            "service_code",
            "revision_id",
            "name",
            "start_date",
            "end_date",
            "origin",
            "destination",
            "journey_description",
            "line_name",
            "stop_sequence",
            "departure_time",
            "is_timing_point",
            "common_name",
            "direction",
            "vehicle_journey_code",
            "line_ref",
            "departure_day_shift",
            "day_of_week",
            "vehicle_journey_id",
            "atco_code",
        ]

        qs_vehicle_journeys = (
            Service.objects.filter(
                revision_id=self._revision_id,
                service_code=self._service_code,
                service_patterns__line_name=self._line_name,
                service_patterns__service_pattern_stops__vehicle_journey__id=F(
                    "service_patterns__service_pattern_vehicle_journey__id"
                ),
            )
            .annotate(
                service_code_s=F("service_code"),
                revision_id_s=F("revision_id"),
                service_name_s=F("name"),
                start_date_s=F("start_date"),
                end_date_s=F("end_date"),
                origin=F("service_patterns__origin"),
                destination=F("service_patterns__destination"),
                journey_description=F("service_patterns__description"),
                line_name=F("service_patterns__line_name"),
                stop_sequence=F(
                    "service_patterns__service_pattern_stops__sequence_number"
                ),
                departure_time=F(
                    "service_patterns__service_pattern_stops__departure_time"
                ),
                is_timing_point=F(
                    "service_patterns__service_pattern_stops__is_timing_point"
                ),
                common_name=Coalesce(
                    "service_patterns__service_pattern_stops__naptan_stop__common_name",
                    "service_patterns__service_pattern_stops__txc_common_name",
                    output_field=CharField(),
                ),
                atco_code=F(
                    "service_patterns__service_pattern_stops__atco_code",
                ),
                direction=F(
                    "service_patterns__service_pattern_vehicle_journey__direction"
                ),
                vehicle_journey_code=F(
                    "service_patterns__service_pattern_vehicle_journey__journey_code"
                ),
                line_ref=F(
                    "service_patterns__service_pattern_vehicle_journey__line_ref"
                ),
                departure_day_shift=F(
                    "service_patterns__service_pattern_vehicle_journey__departure_day_shift"
                ),
                day_of_week=F(
                    "service_patterns__service_pattern_vehicle_journey__operating_profiles__day_of_week"
                ),
                vehicle_journey_id=F(
                    "service_patterns__service_pattern_vehicle_journey__id"
                ),
            )
            .values(*columns)
        )

        return pd.DataFrame.from_records(qs_vehicle_journeys)

    def get_timetable_visualiser(self) -> pd.DataFrame:
        """
        Get the timetable visualiser for the specific service code, revision id,
        line name and the date
        """

        # Create the dataframes for the serviced organisation and service tables.
        df_base_vehicle_journeys = self.get_df_all_vehicle_journeys()
        df_base_vehicle_journeys.to_csv("test_base_vehicle_journey.csv")
        base_vehicle_journey_ids = (
            df_base_vehicle_journeys["vehicle_journey_id"].unique().tolist()
        )
        df_op_excep_vehicle_journey = self.get_df_op_exceptions_vehicle_journey(
            base_vehicle_journey_ids
        )
        df_op_excep_vehicle_journey.to_csv(
            "test_operating_exception_vehicle_journey.csv"
        )
        df_nonop_except_vehicle_journey = self.get_df_nonop_exceptions_vehicle_journey(
            base_vehicle_journey_ids
        )
        df_nonop_except_vehicle_journey.to_csv(
            "test_nonoperating_exception_vehicle_journey.csv"
        )
        df_serviced_org = self.get_df_servicedorg_vehicle_journey(
            base_vehicle_journey_ids
        )
        df_serviced_org.to_csv("test_serviced_organisation_working_days.csv")

        # Get the list of operating and non-operating vehicle journey in the exception table
        (
            op_exception_vehicle_journeys,
            nonop_exception_vehicle_journeys,
            all_exception_vehicle_journeys,
        ) = get_vehicle_journeys_operating_nonoperating(
            df_op_excep_vehicle_journey, df_nonop_except_vehicle_journey
        )

        # Get the vehicle journeys which are operating on the target date based on exception and non-exception
        df_vehicle_journey_operating = get_df_operating_vehicle_journey(
            self._day_of_week,
            df_base_vehicle_journeys,
            op_exception_vehicle_journeys,
            nonop_exception_vehicle_journeys,
        )

        # Get the vehicle journey id which are operating/non-operating for the serviced organisation
        (
            vehicle_journey_ids_op_serviced_org,
            vehicle_journey_ids_nonop_serviced_org,
        ) = filter_df_serviced_org_operating(
            self._target_date, df_serviced_org, all_exception_vehicle_journeys
        )

        # Remove the vehicle journeys which are not running for serviced organisation
        df_vehicle_journey_operating = df_vehicle_journey_operating[
            ~df_vehicle_journey_operating["vehicle_journey_id"].isin(
                vehicle_journey_ids_nonop_serviced_org
            )
        ]

        # Include the vehicle journey id which are not part of base vehicle journey
        base_vehicle_journey_ids = df_vehicle_journey_operating[
            "vehicle_journey_id"
        ].unique()
        vehicle_journey_ids_op_serviced_org = set(vehicle_journey_ids_op_serviced_org)
        if not vehicle_journey_ids_op_serviced_org.issubset(
            set(base_vehicle_journey_ids)
        ):
            vehicle_journey_id_missing = (
                vehicle_journey_ids_op_serviced_org - base_vehicle_journey_ids
            )
            df_vehicle_journey_serviced_org = df_base_vehicle_journeys[
                df_base_vehicle_journeys["vehicle_journey_id"].isin(
                    vehicle_journey_id_missing
                )
            ]

        df_vehicle_journey_operating.to_csv("test_vehicle_journey_operating.csv")
        df_timetable = get_df_timetable_visualiser(df_vehicle_journey_operating)

        return df_timetable
