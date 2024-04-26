""" loaders.py utility functions for loading data into the BODS database."""
import logging
from collections import namedtuple
import pandas as pd

from transit_odp.organisation.models import DatasetRevision
from transit_odp.transmodel.models import Service, ServicePattern, ServicePatternStop

logger = logging.getLogger(__name__)

BATCH_SIZE = 2000


def add_service_associations(
    services: pd.DataFrame, service_patterns: pd.DataFrame
) -> list:
    """
    Add associations between services and service patterns.
    DataFrames are expected to have columns 'id_service' and 'id_service_pattern'.
    """
    through_model = Service.service_patterns.through

    def _inner(df):
        for record in df[["id_service", "id_service_pattern"]].to_dict("records"):
            yield through_model(
                service_id=record["id_service"],
                servicepattern_id=record["id_service_pattern"],
            )

    service_to_service_patterns = services[["id"]].merge(
        service_patterns.reset_index()[["file_id", "service_code", "id"]],
        left_index=True,
        right_on=["file_id", "service_code"],
        suffixes=["_service", "_service_pattern"],
    )
    service_to_service_patterns.drop_duplicates(inplace=True)

    return through_model.objects.bulk_create(_inner(service_to_service_patterns))


def add_service_pattern_to_localities(dataframe):
    """Creates links between ServicePattern objects and Localitys.

    Args:
        dataframe: Pandas DataFrame containing an `id` and `localities`.

    Returns:
        None

    """
    logger.info("Adding service pattern to localities.")
    Locality = namedtuple("Locality", "servicepattern_id,locality_id")
    LocalityThrough = ServicePattern.localities.through
    localities = []
    for record in dataframe.to_dict("records"):
        for locality_id in record["localities"]:
            if locality_id and locality_id != "None":
                localities.append(Locality(record["id"], locality_id))

    localities = set(localities)
    localities = [LocalityThrough(**locality._asdict()) for locality in localities]
    LocalityThrough.objects.bulk_create(localities, batch_size=BATCH_SIZE)


def add_service_pattern_to_admin_area(dataframe):
    """Creates links between ServicePattern objects and AdminAreas.

    Args:
        dataframe: Pandas DataFrame containing an `id` and `admin_area_codes`.

    Returns:
        None

    """

    logger.info("Adding service pattern to admin areas.")
    AdminArea = namedtuple("AdminArea", "servicepattern_id,adminarea_id")
    AdminAreaThrough = ServicePattern.admin_areas.through
    areas = []
    for record in dataframe.to_dict("records"):
        for area_id in record["admin_area_codes"]:
            if area_id:
                areas.append(AdminArea(record["id"], area_id))

    areas = set(areas)
    areas = [AdminAreaThrough(**area._asdict()) for area in areas]
    AdminAreaThrough.objects.bulk_create(areas, batch_size=BATCH_SIZE)


def add_service_pattern_to_localities_and_admin_area(df):
    # Get implicit through-table for m2m
    locality_through_model = ServicePattern.localities.through

    def _inner_localities():
        the_localities = set()
        for record in df.to_dict("records"):
            for locality in record["localities"]:
                if locality and locality != "None":
                    the_localities.add(locality)

            for locality_id in list(the_localities):
                if locality_id:
                    yield locality_through_model(
                        servicepattern_id=record["id"], locality_id=locality_id
                    )

    _localities = list(_inner_localities())
    localities = None
    if len(_localities) > 0:
        localities = locality_through_model.objects.bulk_create(_localities)

    admin_area_through_model = ServicePattern.admin_areas.through

    def _inner_admin_areas():
        the_admin_areas = set()
        for record in df.to_dict("records"):
            for admin_area in record["admin_area_codes"]:
                if admin_area:
                    the_admin_areas.add(admin_area)

            for admin_area_id in list(the_admin_areas):
                if admin_area_id:
                    yield admin_area_through_model(
                        servicepattern_id=record["id"],
                        adminarea_id=admin_area_id,
                    )

    _admin_areas = list(_inner_admin_areas())
    admin_areas = None
    if len(_admin_areas) > 0:
        admin_areas = admin_area_through_model.objects.bulk_create(_admin_areas)
    return localities, admin_areas


def add_service_pattern_to_service_pattern_stops(
    df: pd.DataFrame, service_patterns: pd.DataFrame
) -> list[ServicePatternStop]:
    """Load data onto service pattern stop after mapping service patterns and vehicle journey"""

    logger.info("Adding service_pattern to service pattern stops")

    def _inner():
        for record in df.to_dict("records"):
            service_pattern_id = record.get("service_db_id", None)
            vehicle_journey_id = record.get("id", None)
            sequence_number = record["sequence_number"]
            if not sequence_number:
                sequence_number = record["order"]
            yield ServicePatternStop(
                service_pattern_id=service_pattern_id,
                sequence_number=sequence_number,
                naptan_stop_id=record["naptan_id"],
                atco_code=record["stop_atco"],
                departure_time=record["departure_time"],
                is_timing_point=record["is_timing_status"],
                txc_common_name=record["common_name"],
                vehicle_journey_id=vehicle_journey_id,
            )

    stops = list(_inner())
    if stops:
        return ServicePatternStop.objects.bulk_create(stops, batch_size=BATCH_SIZE)


def create_feed_name(
    most_common_district, first_service_start, no_of_lines, lines, revision
):
    logger.info("Creating feed name.")
    first_service_start = first_service_start.strftime("%Y%m%d")

    # TODO - make functional - easier to test
    organisation = revision.dataset.organisation.name

    if no_of_lines == 1:
        # Case 1, there is one line
        area = most_common_district[0]
        # line_string = lines[0]
        feed_name = f"{organisation}_{area}_{lines}_{first_service_start}"

    elif no_of_lines > 1:
        # Case 2, there are more than one lines
        area = "_".join(most_common_district[:2])
        feed_name = f"{organisation}_{area}_{first_service_start}"
    else:
        # not sure what could have happened here
        # just return the original name
        return revision.name

    # double check there are no clashes
    match = list(
        DatasetRevision.objects.filter(name__startswith=feed_name)
        .values("name")
        .order_by("name")
    )
    if not match:
        # nope we are good to go
        return feed_name

    if len(match) == 1 and match[0]["name"] == feed_name:
        # the first duplicate
        return f"{feed_name}_1"

    # We know the first element is the feed name without underscores
    # if it exists chop it out
    if match[0]["name"] == feed_name:
        match.pop(0)

    highest_match = max(match, key=lambda n: int(n["name"].split("_")[-1]))
    highest_match = highest_match["name"]

    # we just need to append increment end by 1
    clash_count = int(highest_match.split("_")[-1])
    clash_count += 1
    return f"{feed_name}_{clash_count}"
