STATUSES = {
    "PENDING": "PENDING",
}
CHECKS_DATA = [
    {
        "observation": "Incorrect NOC",
        "importance": "Critical",
        "category": "Data set",
        "queue_name": "incorrect_noc_queue",
    },
    {
        "observation": "First stop is set down only",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "first_stop_is_set_down_only_queue",
    },
    {
        "observation": "Last stop is pick up only",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "last_stop_is_pickup_only_queue",
    },
    {
        "observation": "First stop is not a timing point",
        "importance": "Critical",
        "category": "Timing",
        "queue_name": "first_step_is_not_a_timing_point_queue",
    },
    {
        "observation": "Last stop is not a timing point",
        "importance": "Critical",
        "category": "Timing",
        "queue_name": "last_stop_is_not_a_timing_point_queue",
    },
    {
        "observation": "Incorrect stop type",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "incorrect_stop_type_queue",
    },
    {
        "observation": "Missing journey code",
        "importance": "Critical",
        "category": "Journey",
        "queue_name": "missing_journey_code_queue",
    },
    {
        "observation": "Duplicate journey code",
        "importance": "Critical",
        "category": "Journey",
        "queue_name": "duplicate_journey_code_queue",
    },
    {
        "observation": "Missing bus working number",
        "importance": "Advisory",
        "category": "Journey",
        "queue_name": "missing_bus_working_number_queue",
    },
    {
        "observation": "Missing stops",
        "importance": "Advisory",
        "category": "Stop",
        "queue_name": "missing_stops_queue",
    },
    {
        "observation": "Stop(s) not found in NaPTAN",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "stops_not_found_in_queue",
    },
    {
        "observation": "Same stop found multiple times",
        "importance": "Advisory",
        "category": "Stop",
        "queue_name": "same_stop_found_multiple_times_queue",
    },
    {
        "observation": "Incorrect licence number",
        "importance": "Critical",
        "category": "Data set",
        "queue_name": "incorrect_licence_number_queue",
    },
]
