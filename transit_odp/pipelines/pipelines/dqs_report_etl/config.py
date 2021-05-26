from typing import Dict

MODEL_CONFIG: Dict[str, Dict] = {
    "stops": {
        "columns": [
            "id",
            "geometry",
            "atco_code",
            "bearing",
            "feature_name",
            "type",
            "synthetic",
        ],
        "rename_columns": {"id": "ito_id", "feature_name": "name"},
        "index_column": "ito_id",
        "geojson": True,
    },
    "lines": {
        "columns": ["id", "name"],
        "geojson": False,
        "rename_columns": {"id": "ito_id"},
        "index_column": "ito_id",
    },
    "service_patterns": {
        "columns": [
            "geometry",
            "feature_name",
            "length_m",
            "id",
            "line",
            "stops",
            "timing_patterns",
            "service_links",
        ],
        "rename_columns": {"id": "ito_id", "feature_name": "name"},
        "index_column": "ito_id",
        "geojson": True,
    },
    "service_links": {
        "columns": [
            "id",
            "geometry",
            "feature_name",
            "from_stop",
            "length_m",
            "to_stop",
        ],
        "rename_columns": {"id": "ito_id", "feature_name": "name"},
        "index_column": "ito_id",
        "geojson": True,
    },
    "timing_patterns": {
        "columns": ["id", "service_pattern", "timings", "vehicle_journeys"],
        "rename_columns": {"id": "ito_id", "service_pattern": "service_pattern_ito_id"},
        "index_column": "ito_id",
        "geojson": False,
    },
    "vehicle_journeys": {
        "columns": [
            "id",
            "timing_pattern",
            "start",
            "feature_name",
            "dates",
            # "source",
            # "source_id",
        ],
        "rename_columns": {
            "id": "ito_id",
            "feature_name": "name",
            "timing_pattern": "timing_pattern_ito_id",
        },
        "index_column": "ito_id",
        "geojson": False,
    },
}
WARNING_CONFIG: Dict[str, Dict] = {
    "service_link_missing_stops": {
        "columns": [
            "id",
            "warning_type",
            "warning_id",
            "from_stop",
            "to_stop",
            "stops",
            "service_patterns",
        ],
        "rename_columns": {"warning_id": "ito_id", "id": "service_link_ito_id"},
    },
    "timing_missing_point_15": {
        "columns": ["id", "warning_type", "warning_id", "missing_stop", "indexes"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "timing_multiple": {
        "columns": ["id", "warning_type", "warning_id", "indexes"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "timing_first": {
        "columns": ["id", "warning_type", "warning_id", "indexes"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "timing_last": {
        "columns": ["id", "warning_type", "warning_id", "indexes"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "timing_fast_link": {
        "columns": ["id", "warning_type", "warning_id", "indexes", "service_link"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "timing_fast": {
        "columns": ["id", "warning_type", "warning_id", "indexes", "entities"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "timing_slow": {
        "columns": ["id", "warning_type", "warning_id", "indexes", "entities"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "timing_slow_link": {
        "columns": ["id", "warning_type", "warning_id", "indexes", "service_link"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "timing_backwards": {
        "columns": ["id", "warning_type", "warning_id", "indexes"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "timing_pick_up": {
        "columns": ["id", "warning_type", "warning_id", "indexes"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "timing_drop_off": {
        "columns": ["id", "warning_type", "warning_id", "indexes"],
        "rename_columns": {"warning_id": "ito_id", "id": "timing_pattern_ito_id"},
    },
    "journeys_without_headsign": {
        "columns": ["id", "warning_type", "warning_id"],
        "rename_columns": {"warning_id": "ito_id", "id": "vehicle_journey_ito_id"},
    },
    "journey_duplicate": {
        "columns": ["id", "warning_type", "warning_id", "duplicate"],
        "rename_columns": {"warning_id": "ito_id", "id": "vehicle_journey_ito_id"},
    },
    "journey_conflict": {
        "columns": ["id", "warning_type", "warning_id", "conflict", "stops"],
        "rename_columns": {"warning_id": "ito_id", "id": "vehicle_journey_ito_id"},
    },
    "journey_date_range_backwards": {
        "columns": ["id", "warning_type", "warning_id", "start", "end"],
        "rename_columns": {"warning_id": "ito_id", "id": "vehicle_journey_ito_id"},
    },
    "stop_missing_naptan": {
        "columns": ["id", "warning_type", "warning_id", "service_patterns"],
        "rename_columns": {"warning_id": "ito_id", "id": "stop_ito_id"},
    },
    "stop_incorrect_type": {
        "columns": [
            "id",
            "warning_type",
            "warning_id",
            "stop_type",
            "service_patterns",
        ],
        "rename_columns": {"warning_id": "ito_id", "id": "stop_ito_id"},
    },
    "journey_stop_inappropriate": {
        "columns": [
            "id",
            "warning_type",
            "warning_id",
            "stop_type",
            "vehicle_journeys",
        ],
        "rename_columns": {"warning_id": "ito_id", "id": "stop_ito_id"},
    },
}
