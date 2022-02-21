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
