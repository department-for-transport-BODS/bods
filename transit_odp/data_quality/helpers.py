def create_comma_separated_string(iterable):
    return ",".join(map(str, iterable))


def convert_date_to_dmY_string(date_object):
    try:
        date_string = date_object.strftime("%d/%m/%Y")
    except (AttributeError, ValueError):
        date_string = "unknown date"
    finally:
        return date_string


def convert_time_to_HMS_string(time_object):
    return time_object.strftime("%H:%M:%S")


# Used in journey_overlap views and tables (not ideal to have it here, but getting
# circular imports otherwise)
def construct_journey_overlap_message(warning):
    def get_stop_name(vehicle_journey):
        service_pattern_stops = (
            vehicle_journey.timing_pattern.service_pattern.service_pattern_stops
        )
        return service_pattern_stops.earliest("position").stop.name

    start_time_1 = convert_time_to_HMS_string(warning.vehicle_journey.start_time)
    start_time_2 = convert_time_to_HMS_string(warning.conflict.start_time)
    from_stop_1 = get_stop_name(warning.vehicle_journey)
    from_stop_2 = get_stop_name(warning.conflict)
    return (
        f"{start_time_1} from {from_stop_1} and "
        f"{start_time_2} from {from_stop_2} overlaps"
    )
