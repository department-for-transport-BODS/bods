import attr


@attr.s(auto_attribs=True)
class RangeFilter(object):
    # A range to filter on
    filter: str
    display: str
    disabled: bool
