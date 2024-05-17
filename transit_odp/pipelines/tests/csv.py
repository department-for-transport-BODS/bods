import sys
import pandas as pd


file_path = "transit_odp/pipelines/tests/test_dataset_etl/data/csv/test"
file_prefix = "with_vj_operating_profile_multi_serviced_org"

# Invoke this method from below path to print csv files required for unit tests
# transit_odp/browse/timetable_visualiser.py
def print_csv_with_db_data(
    base_qs_vehicle_journeys: pd.DataFrame,
    df_nonop_excep_vehicle_journey: pd.DataFrame,
    df_op_excep_vehicle_journey: pd.DataFrame,
    df_serviced_org: pd.DataFrame,
    disable_csv=True,
):
    if "pytest" not in sys.modules and not disable_csv:
        print_csv = pd.DataFrame.from_records(base_qs_vehicle_journeys)
        print_csv.to_csv(f"{file_path}/{file_prefix}_base.csv", index=False)
        df_nonop_excep_vehicle_journey.to_csv(
            f"{file_path}/{file_prefix}_non_op_excep.csv", index=False
        )
        df_op_excep_vehicle_journey.to_csv(
            f"{file_path}/{file_prefix}_op_excep.csv", index=False
        )
        df_serviced_org.to_csv(f"{file_path}/{file_prefix}_so_data.csv", index=False)


# Invoke this method from below path to print inbound and outbound csv files required for unit tests
# These files would contain the inbound and outbound dataframes sent to the ui and
# the below function should be added within the for loop in timetable_visualiser
# transit_odp/browse/timetable_visualiser.py
def print_csv_with_timetable_data(df_timetable, direction, disable_csv=True):
    if "pytest" not in sys.modules and not disable_csv:
        df_timetable.to_csv(
            f"{file_path}/{file_prefix}_{direction}_final.csv", index=False
        )
