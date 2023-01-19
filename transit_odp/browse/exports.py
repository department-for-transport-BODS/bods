import io
import logging
import zipfile
from collections import namedtuple
from typing import BinaryIO

from transit_odp.avl.csv.catalogue import AVL_COLUMN_MAP, get_avl_data_catalogue_csv
from transit_odp.browse.constants import INTRO
from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.organisation.constants import ERROR, LIVE, NO_ACTIVITY, AVLType
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.organisation.csv.organisation import (
    ORG_COLUMN_MAP,
    get_organisation_catalogue_csv,
)
from transit_odp.organisation.csv.overall import (
    OVERALL_COLUMN_MAP,
    get_overall_data_catalogue_csv,
)
from transit_odp.organisation.models import Organisation
from transit_odp.timetables.csv import TIMETABLE_COLUMN_MAP, get_timetable_catalogue_csv

logger = logging.getLogger(__name__)

CSVFile = namedtuple("CSVFile", "name, builder")
GUIDANCE_TEMPLATE = "browse/guideme/data_catalogue_guidance.txt"
GUIDANCE_FILENAME = "data_catalogue_guidance.txt"
ORGANISATION_FILENAME = "organisations_data_catalogue.csv"
TIMETABLE_FILENAME = "timetables_data_catalogue.csv"
OVERALL_FILENAME = "overall_data_catalogue.csv"
LOCATION_FILENAME = "location_data_catalogue.csv"
NOC_FILENAME = "operator_noc_data_catalogue.csv"
OTC_EMPTY_WARNING = "OTC Licence is not populated."


def get_feed_status(dataset):
    if dataset.dataset_type == AVLType and dataset.live_revision.status == ERROR:
        return NO_ACTIVITY
    if dataset.live_revision.status == LIVE:
        return "Published"

    return dataset.live_revision.status.capitalize()


class DownloadOperatorNocCatalogueCSV(CSVBuilder):
    columns = [
        CSVColumn(header="operator", accessor="name"),
        CSVColumn(header="noc", accessor="nocs_string"),
    ]

    def get_queryset(self):
        qs = (
            Organisation.objects.filter(is_active=True)
            .add_nocs_string()
            .order_by("name", "nocs__noc")
        )
        return qs


def create_guidance_file_string() -> str:
    row_template = "{field_name:45}{definition}"
    header_template = "{header}\n{field_header:45}Definition"
    field_header = "Field name"

    result = [INTRO]

    overall = "Overall data catalogue:"
    result.append(header_template.format(header=overall, field_header=field_header))
    result += [
        row_template.format(field_name=field_name, definition=definition)
        for field_name, definition in OVERALL_COLUMN_MAP.values()
    ]

    timetables = "\nTimetables data catalogue:"
    result.append(header_template.format(header=timetables, field_header=field_header))
    result += [
        row_template.format(field_name=field_name, definition=definition)
        for field_name, definition in TIMETABLE_COLUMN_MAP.values()
    ]

    organisations = "\nOrganisations data catalogue:"
    result.append(
        header_template.format(header=organisations, field_header=field_header)
    )
    result += [
        row_template.format(field_name=field_name, definition=definition)
        for field_name, definition in ORG_COLUMN_MAP.values()
    ]

    locations = "\nLocation data catalogue:"
    result.append(header_template.format(header=locations, field_header=field_header))
    result += [
        row_template.format(field_name=field_name, definition=definition)
        for field_name, definition in AVL_COLUMN_MAP.values()
    ]

    return "\n".join(result)


def create_data_catalogue_file() -> BinaryIO:
    buffer_ = io.BytesIO()
    files = (CSVFile(NOC_FILENAME, DownloadOperatorNocCatalogueCSV),)

    with zipfile.ZipFile(buffer_, mode="w", compression=zipfile.ZIP_DEFLATED) as zin:
        for file_ in files:
            Builder = file_.builder
            zin.writestr(file_.name, Builder().to_string())

        try:
            zin.writestr(ORGANISATION_FILENAME, get_organisation_catalogue_csv())
        except EmptyDataFrame as exc:
            logger.warning(OTC_EMPTY_WARNING, exc_info=exc)

        zin.writestr(GUIDANCE_FILENAME, create_guidance_file_string())

        try:
            zin.writestr(TIMETABLE_FILENAME, get_timetable_catalogue_csv())

        except EmptyDataFrame as exc:
            logger.warning(OTC_EMPTY_WARNING, exc_info=exc)

        try:
            zin.writestr(OVERALL_FILENAME, get_overall_data_catalogue_csv())
        except EmptyDataFrame:
            pass

        try:
            zin.writestr(LOCATION_FILENAME, get_avl_data_catalogue_csv())
        except EmptyDataFrame:
            pass

    buffer_.seek(0)
    return buffer_
