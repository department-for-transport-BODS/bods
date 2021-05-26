def to_int_or_value(value):
    """Either cast an object to an integer else return the original object."""
    try:
        return int(value)
    except ValueError:
        return value
