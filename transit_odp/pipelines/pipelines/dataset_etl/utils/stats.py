import pandas as pd


def get_transformed_stats(transformed):
    stats = pd.DataFrame(
        {
            "count": [
                transformed.services.shape[0],
                transformed.service_patterns.shape[0],
                transformed.service_pattern_to_service_links.shape[0],
                transformed.service_links.shape[0],
                transformed.stop_points.shape[0],
            ],
            "name": [
                "service",
                "service_patterns",
                "service_pattern_to_service_links",
                "service_links",
                "stop_points",
            ],
        }
    ).set_index("name")
    return stats


def get_extracted_stats(extracted):
    stats = pd.DataFrame(
        {
            "count": [
                extracted.services.shape[0],
                extracted.stop_points.shape[0],
                extracted.journey_patterns.shape[0],
                extracted.jp_to_jps.shape[0],
                extracted.jp_sections.shape[0],
                extracted.timing_links.shape[0],
            ],
            "name": [
                "service",
                "stop_points",
                "journey_patterns",
                "jp_to_jps",
                "jp_sections",
                "timing_links",
            ],
        }
    ).set_index("name")
    return stats
