import os
from typing import Dict, List, Set

from django.contrib.gis.geos import Point
from django.core.files import File

from transit_odp.naptan.models import AdminArea, District, Locality, StopPoint
from transit_odp.pipelines.pipelines.dataset_etl.feed_parser import FeedParser
from transit_odp.pipelines.pipelines.dataset_etl.xml_file_parser import XmlFileParser
from transit_odp.pipelines.pipelines.dataset_etl.zip_file_parser import ZipFileParser


def create_naptan_stops(
    feed_parser: FeedParser,
    file_obj: File,
    localities: List[Locality],
    admin_area: AdminArea,
):
    """
    Create naptan stops contained in the given file.
    The file can be a single xml file or a zip.
    """

    def _process_file(
        localities: Dict[str, Locality],
        stop_points: Dict[str, StopPoint],
        filepath: str,
    ):

        file_obj = File(filepath, name=os.path.basename(filepath))
        doc = parser.parse_document(file_obj)

        _stop_points = parser.xml_toolkit.get_elements(
            doc, "/x:TransXChange/x:StopPoints/x:AnnotatedStopPointRef"
        )
        for stop_point in _stop_points:
            atco_code = parser.xml_toolkit.get_child_text(stop_point, "x:StopPointRef")
            if atco_code not in stop_points:
                locality = parser.xml_toolkit.get_child_text(
                    stop_point, "x:LocalityName"
                )
                stop_point = StopPoint(
                    atco_code=atco_code,
                    common_name=parser.xml_toolkit.get_child_text(
                        stop_point, "x:CommonName"
                    ),
                    location=Point(x=0, y=0),
                    locality=localities[locality],
                    admin_area=admin_area,
                )
                stop_points[atco_code] = stop_point

    # Build a map from locality name to locality
    _localities = {}
    for locality in localities:
        _localities[locality.name] = locality

    filename = file_obj.file
    parser = XmlFileParser(feed_parser)
    stop_points = {}

    if filename.endswith("zip"):
        # Unzip and walk the directories
        zip_extractor = ZipFileParser(feed_parser, feed_parser.feed_task_result)
        tmpdirname, files = zip_extractor.unzip(file_obj)
        for root, dirs, files in os.walk(tmpdirname.name):
            for file in files:
                filepath = os.path.join(root, file)
                _process_file(_localities, stop_points, filepath)

    elif filename.endswith("xml"):
        _process_file(_localities, stop_points, filename)
    else:
        raise Exception("Invalid filename extension %s" % filename)

    StopPoint.objects.bulk_create(list(stop_points.values()))


def create_naptan_localities(
    feed_parser: FeedParser,
    file_obj: File,
    default_admin_area: AdminArea,
    default_district: District,
):

    """
    Create naptan localities contained in the given file, attaching them to the
    default_admin_area.
    The file can be a single xml file or a zip.
    """

    def _process_file(localities: Set[str], filepath: str):

        file_obj = File(filepath, name=os.path.basename(filepath))
        doc = parser.parse_document(file_obj)

        _stop_points = parser.xml_toolkit.get_elements(
            doc, "/x:TransXChange/x:StopPoints/x:AnnotatedStopPointRef"
        )
        for stop_point in _stop_points:
            locality_name = parser.xml_toolkit.get_child_text(
                stop_point, "x:LocalityName"
            )
            localities.add(locality_name)

    def _inner(localities: Set[str]):
        for index, name in enumerate(list(localities)):
            locality = Locality(
                gazetteer_id=f"LO{str(index)}",
                name=name,
                district=default_district,
                admin_area=default_admin_area,
                easting=0,
                northing=0,
                # last_change=now,
            )
            yield locality

    parser = XmlFileParser(feed_parser)
    localities = set()

    filename = file_obj.file

    if filename.endswith("zip"):
        # Unzip and walk the directories
        zip_extractor = ZipFileParser(feed_parser, feed_parser.feed_task_result)
        tmpdirname, files = zip_extractor.unzip(file_obj)
        for root, dirs, files in os.walk(tmpdirname.name):
            for file in files:
                filepath = os.path.join(root, file)
                _process_file(localities, filepath)

    elif filename.endswith("xml"):
        _process_file(localities, filename)
    else:
        raise Exception("Invalid filename extension %s" % filename)

    _localities = Locality.objects.bulk_create(list(_inner(localities)))
    return _localities
