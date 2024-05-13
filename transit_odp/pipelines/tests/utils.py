import pandas as pd
from pandas.testing import assert_frame_equal


def check_frame_equal(df1, df2, **kwargs) -> bool:
    """Compare that two dataframes are equal ignoring ordering of columns and rows"""

    try:
        assert_frame_equal_basic(df1, df2, **kwargs)
        return True
    except Exception:
        return False


def assert_frame_equal_basic(df1, df2, **kwargs):
    """Asserts df1 equals df2 when index and columns are sorted"""
    assert_frame_equal(
        df1.sort_index(axis=0).sort_index(axis=1),
        df2.sort_index(axis=0).sort_index(axis=1),
        check_names=True,
        **kwargs
    )


def modify_time_columns(df: pd.DataFrame, time_columns: list) -> pd.DataFrame:
    for col in time_columns:
        df[col] = pd.to_datetime(df[col], format="%H:%M:%S")
        df[col] = df[col].dt.time

    return df


def modify_date_columns(df: pd.DataFrame, date_columns: list) -> pd.DataFrame:
    for col in date_columns:
        df[col] = pd.to_datetime(df[col])
    return df


def get_base_csv(file_name_with_path: str) -> pd.DataFrame:
    date_columns = ["start_date", "end_date"]
    base_csv = pd.read_csv(file_name_with_path)
    base_csv = modify_date_columns(base_csv, date_columns)
    base_csv["departure_time"] = pd.to_datetime(
        base_csv["departure_time"], format="%H:%M:%S"
    )
    base_csv["departure_time"] = base_csv["departure_time"].dt.time

    return base_csv


def get_serviced_org_csv(file_name_with_path: str) -> pd.DataFrame:
    date_columns = ["start_date", "end_date"]
    serviced_org = pd.read_csv(file_name_with_path)
    serviced_org = modify_date_columns(serviced_org, date_columns)
    return serviced_org
