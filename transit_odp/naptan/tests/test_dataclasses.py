import pytest

from transit_odp.naptan.dataclasses import StopPoint


def test_north_east_stop_from_xml(ukos_stop):
    """
    GIVEN an lxml naptan:StopPoint with northing and easting
    WHEN I call `from_xml`
    THEN a StopPoint is created with a translation to Lat/Long.
    """
    point = StopPoint.from_xml(ukos_stop)
    assert point.atco_code == "0100BRP90310"
    assert point.naptan_code == "bstgwpa"
    assert point.descriptor.common_name == "Temple Meads Stn"
    assert point.descriptor.short_common_name == "Temple Meads Stn"
    assert point.descriptor.street == "Redcliffe Way"
    assert point.descriptor.indicator == "T3"
    assert point.place.nptg_locality_ref == "N0077020"
    assert point.place.location.grid_type == "UKOS"
    assert point.place.location.easting == 359396
    assert point.place.location.northing == 172388
    assert pytest.approx(point.place.location.translation.longitude, 0.001) == -2.585688
    assert pytest.approx(point.place.location.translation.latitude, 0.001) == 51.449013
    assert point.place.location.translation.grid_type == "UKOS"
    assert point.place.location.translation.easting == 359396
    assert point.place.location.translation.northing == 172388
    assert point.administrative_area_ref == "009"
    assert point.stop_classification.stop_type == "BCT"
    assert point.stop_classification.on_street.bus.bus_stop_type == "MKD"


def test_wgs_stop_from_xml(wgs_stop):
    """
    GIVEN an lxml naptan:StopPoint with latitude and longitude
    WHEN I call `from_xml`
    THEN a StopPoint is created with a translation containing lat/long and
    easting/northing.
    """
    point = StopPoint.from_xml(wgs_stop)
    assert point.atco_code == "036000003079"
    assert point.naptan_code == "wingdjw"
    assert point.descriptor.common_name == "Square Deal Cafe"
    assert point.descriptor.short_common_name is None
    assert point.descriptor.street == "Bath Road A4"
    assert point.descriptor.indicator == "adj"
    assert point.place.nptg_locality_ref == "E0043279"
    assert point.place.location.grid_type is None
    assert point.place.location.easting is None
    assert point.place.location.northing is None
    assert pytest.approx(point.place.location.translation.longitude, 0.001) == -0.815883
    assert pytest.approx(point.place.location.translation.latitude, 0.001) == 51.508047
    assert point.place.location.translation.grid_type == "UKOS"
    assert point.place.location.translation.easting == 482276
    assert point.place.location.translation.northing == 179455
    assert point.administrative_area_ref == "065"
    assert point.stop_classification.stop_type == "BCT"
    assert point.stop_classification.on_street.bus.bus_stop_type == "MKD"


def test_stop_with_multiple_stop_areas_xml(multiple_stop_areas_stop):
    """
    GIVEN an lxml naptan:StopPoint with multiple stop areas
    WHEN I call `from_xml`
    THEN a StopPoint is created with a list of stop areas
    """
    point = StopPoint.from_xml(multiple_stop_areas_stop)
    assert sorted(point.stop_areas) == ["036G00006160", "036G00006161"]


def test_flexible_stop_from_xml(flexible_stops):
    """
    GIVEN an lxml naptan:StopPoint with flexible zone bus type
    WHEN I call `from_xml`
    THEN a StopPoint and Flexible Zone is created with a translation containing lat/long and
    easting/northing.
    """
    point = StopPoint.from_xml(flexible_stops)
    assert point.atco_code == "030058840001"
    assert point.naptan_code == "brkpwdg"
    assert point.descriptor.common_name == "Englefield flexi area"
    assert point.descriptor.short_common_name is None
    assert point.descriptor.street == "The Street"
    assert point.descriptor.indicator == "DRT"
    assert point.place.nptg_locality_ref == "E0053838"
    assert point.place.location.grid_type is None
    assert point.place.location.easting is None
    assert point.place.location.northing is None
    assert pytest.approx(point.place.location.translation.longitude, 0.001) == -1.099
    assert pytest.approx(point.place.location.translation.latitude, 0.001) == 51.44
    assert point.place.location.translation.grid_type == "UKOS"
    assert point.place.location.translation.easting == 462732
    assert point.place.location.translation.northing == 172119
    assert point.administrative_area_ref == "064"
    assert point.stop_classification.stop_type == "BCT"
    assert point.stop_classification.on_street.bus.bus_stop_type == "FLX"
    assert len(point.stop_classification.on_street.bus.flexible_zone.location) == 3
    assert (
        point.stop_classification.on_street.bus.flexible_zone.location[0].easting
        == 462732
    )
    assert (
        point.stop_classification.on_street.bus.flexible_zone.location[0].northing
        == 172119
    )
    assert pytest.approx(point.place.location.translation.longitude, 0.001) == -1.099
    assert pytest.approx(point.place.location.translation.latitude, 0.001) == 51.44
