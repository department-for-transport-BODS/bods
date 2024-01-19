from transit_odp.api.app.views import _get_coordinates_from_disruption
from transit_odp.api.app.views import _format_data_for_map


def test_get_coordinates_from_disruption_no_coordinates():
    disruption_with_no_coordinates = [
        {
            "consequenceType": "services",
            "services": [{"coordinates": {"latitude": None, "longitude": None}}],
        },
        {
            "consequenceType": "stops",
            "stops": [{"latitude": None, "longitude": None}],
        },
        {
            "consequenceType": "networkWide",
        },
        {
            "consequenceType": "operatorWide",
        },
    ]

    expected_coordinates = []

    actual_coordinates = _get_coordinates_from_disruption(
        disruption_with_no_coordinates
    )

    assert actual_coordinates == expected_coordinates


def test_get_coordinates_from_disruption_with_coordinates():
    disruption_with_coordinates = [
        {
            "consequenceType": "services",
            "services": [
                {"coordinates": {"latitude": 51.39866, "longitude": -2.29852}}
            ],
        },
        {
            "consequenceType": "stops",
            "stops": [
                {
                    "longitude": -2.39201,
                    "latitude": 51.36445,
                },
            ],
        },
        {
            "consequenceType": "networkWide",
        },
        {
            "consequenceType": "operatorWide",
        },
    ]

    expected_coordinates = [
        {
            "longitude": -2.29852,
            "latitude": 51.39866,
        },
        {
            "longitude": -2.39201,
            "latitude": 51.36445,
        },
    ]

    actual_coordinates = _get_coordinates_from_disruption(disruption_with_coordinates)

    assert actual_coordinates == expected_coordinates


def test_format_data_for_map():
    coordinates = [
        {
            "longitude": -2.29852,
            "latitude": 51.39866,
        },
        {
            "longitude": -2.39201,
            "latitude": 51.36445,
        },
    ]

    disruption_reason = "roadworks"

    expected_map_data = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    -2.29852,
                    51.39866,
                ],
            },
            "properties": {"disruptionReason": "roadworks"},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    -2.39201,
                    51.36445,
                ],
            },
            "properties": {"disruptionReason": "roadworks"},
        },
    ]

    actual_map_data = _format_data_for_map(coordinates, disruption_reason)

    assert actual_map_data == expected_map_data
