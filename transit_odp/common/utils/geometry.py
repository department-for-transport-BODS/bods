import pyproj
from shapely.geometry import Point
from shapely.ops import transform


def grid_gemotry_from_str(easting, northing):
    point = Point(float(easting), float(northing))
    return construct_geometry(point)


def wsg84_from_str(longitude, latitude):
    return Point(float(longitude), float(latitude))


def osgb36_to_wgs84(osgb36_point):
    wgs84 = pyproj.CRS("EPSG:4326")
    osgb36 = pyproj.CRS("EPSG:27700")
    project = pyproj.Transformer.from_crs(osgb36, wgs84, always_xy=True).transform
    wgs84_point = transform(project, osgb36_point)
    return wgs84_point


def construct_geometry(point: Point):
    return osgb36_to_wgs84(point)
