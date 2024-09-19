import math
from datetime import datetime, timedelta

from django.db.models import Max
from django.utils import timezone

from transit_odp.organisation.models import DatasetRevision, TXCFileAttributes
from transit_odp.publish.constants import LICENCE_NUMBER_NOT_SUPPLIED_MESSAGE
from transit_odp.transmodel.models import BookingArrangements, Service


def get_simulated_progress(start_time: datetime, max_minutes: timedelta):
    """Calculates a simulated progress value.
    Assumes that a task will take `max_minutes` minutes to complete.
    """
    elapsed_time = timezone.now() - start_time
    progress = math.floor(100 * elapsed_time / max_minutes)
    progress = min(progress, 99)
    return progress


def get_distinct_dataset_txc_attributes(revision_id):
    txc_attributes = {}
    txc_file_attributes = TXCFileAttributes.objects.filter(revision_id=revision_id)

    for file_attribute in txc_file_attributes:
        licence_number = (
            file_attribute.licence_number
            and file_attribute.licence_number.strip()
            or LICENCE_NUMBER_NOT_SUPPLIED_MESSAGE
        )
        noc_dict = txc_attributes.setdefault(licence_number, {}).setdefault(
            file_attribute.national_operator_code, {}
        )
        for line_name in file_attribute.line_names:
            line_names_dict = noc_dict.setdefault(line_name, set())
            line_names_dict.add(file_attribute.service_code)

    return txc_attributes


def get_revision_details(dataset_id):
    revision_details = []
    revision = DatasetRevision.objects.get(dataset_id=dataset_id)
    revision_details.append(revision.id)
    revision_details.append(revision.name)

    return revision_details


def get_service_type(revision_id, service_code, line_name):
    """
    Determine the service type based on the provided parameters.

    This method queries the database to retrieve service types for a given revision,
    service code, and line name. It then analyzes the retrieved service types to determine
    the overall service type.

    Parameters:
        revision_id (int): The ID of the revision.
        service_code (str): The service code.
        line_name (str): The name of the line.

    Returns:
        str: The determined service type, which can be one of the following:
            - "Standard" if all retrieved service types are "standard".
            - "Flexible" if all retrieved service types are "flexible".
            - "Flexible/Standard" if both "standard" and "flexible" service types are present.
    """
    all_service_types_list = []
    service_types_qs = (
        Service.objects.filter(
            revision=revision_id,
            service_code=service_code,
            name=line_name,
        )
        .values_list("service_type", flat=True)
        .distinct()
    )
    for service_type in service_types_qs:
        all_service_types_list.append(service_type)

    if all(service_type == "standard" for service_type in all_service_types_list):
        return "Standard"
    elif all(service_type == "flexible" for service_type in all_service_types_list):
        return "Flexible"
    return "Flexible/Standard"


def get_current_files(revision_id, service_code, line_name):
    """
    Get the list of current valid files for a given revision, service code, and line name.

    This method retrieves the filenames of the current valid files for a specific revision,
    service code, and line name, considering the operating period start and end dates.

    Parameters:
        revision_id (int): The ID of the revision.
        service_code (str): The service code.
        line_name (str): The name of the line.

    Returns:
        list: A list of dictionaries, each containing information about a valid file, including:
            - "filename": The name of the file.
            - "start_date": The start date of the file's operating period.
            - "end_date": The end date of the file's operating period, if available."""
    valid_file_names = []
    today = datetime.now().date()

    highest_revision_number = TXCFileAttributes.objects.filter(
        revision=revision_id,
        service_code=service_code,
        line_names__contains=[line_name],
    ).aggregate(highest_revision_number=Max("revision_number"))[
        "highest_revision_number"
    ]

    file_name_qs = TXCFileAttributes.objects.filter(
        revision=revision_id,
        service_code=service_code,
        line_names__contains=[line_name],
        revision_number=highest_revision_number,
    ).values_list(
        "filename",
        "operating_period_start_date",
        "operating_period_end_date",
    )

    for file_name in file_name_qs:
        operating_period_start_date = file_name[1]
        operating_period_end_date = file_name[2]

        if operating_period_start_date and operating_period_end_date:
            if (
                operating_period_start_date <= today
                and today <= operating_period_end_date
            ):
                valid_file_names.append(
                    {
                        "filename": file_name[0],
                        "start_date": operating_period_start_date,
                        "end_date": operating_period_end_date,
                    }
                )
        elif operating_period_start_date:
            if operating_period_start_date <= today:
                valid_file_names.append(
                    {
                        "filename": file_name[0],
                        "start_date": operating_period_start_date,
                        "end_date": None,
                    }
                )
        elif operating_period_end_date:
            if today <= operating_period_end_date:
                valid_file_names.append(
                    {
                        "filename": file_name[0],
                        "start_date": None,
                        "end_date": operating_period_end_date,
                    }
                )

    return valid_file_names


def get_most_recent_modification_datetime(revision_id, service_code, line_name):
    """
    Get the most recent modification datetime for a given revision, service code, and line name.

    This function retrieves the maximum modification datetime among all TXC file attributes
    matching the provided revision ID, service code, and line name.

    Parameters:
        revision_id (int): The ID of the revision.
        service_code (str): The service code.
        line_name (str): The name of the line.

    Returns:
        datetime: The most recent modification datetime, or None if no matching records are found.
    """
    return TXCFileAttributes.objects.filter(
        revision_id=revision_id,
        service_code=service_code,
        line_names__contains=[line_name],
    ).aggregate(max_modification_datetime=Max("modification_datetime"))[
        "max_modification_datetime"
    ]


def get_lastest_operating_period_start_date(
    revision_id, service_code, line_name, recent_modification_datetime
):
    """
    Get the latest operating period start date for a given revision, service code,
    line name, and recent modification datetime.

    This method retrieves the maximum start date of the operating period among all TXC
    file attributes matching the provided parameters and having the specified recent
    modification datetime.

    Parameters:
        revision_id (int): The ID of the revision.
        service_code (str): The service code.
        line_name (str): The name of the line.
        recent_modification_datetime (datetime): The most recent modification datetime.

    Returns:
        datetime: The latest operating period start date, or None if no matching records are found.
    """
    return TXCFileAttributes.objects.filter(
        revision_id=revision_id,
        service_code=service_code,
        line_names__contains=[line_name],
        modification_datetime=recent_modification_datetime,
    ).aggregate(max_start_date=Max("operating_period_start_date"))["max_start_date"]


def get_single_booking_arrangements_file(revision_id, service_code):
    """
    Retrieve the booking arrangements details from a single booking arrangements file
    for a given revision ID and service code.

    This function attempts to retrieve service IDs corresponding to the provided revision ID
    and service code. If no matching service IDs are found, it returns None. Otherwise, it
    queries the booking arrangements associated with the retrieved service IDs and returns
    a distinct set of booking arrangements details.

    Parameters:
        revision_id (int): The ID of the revision.
        service_code (str): The service code.

    Returns:
        QuerySet or None"""
    try:
        service_ids = (
            Service.objects.filter(revision=revision_id)
            .filter(service_code=service_code)
            .values_list("id", flat=True)
        )
    except Service.DoesNotExist:
        return None
    return (
        BookingArrangements.objects.filter(service_id__in=service_ids)
        .values_list("description", "email", "phone_number", "web_address")
        .distinct()
    )


def get_valid_files(revision_id, valid_files, service_code, line_name):
    """
    Get the valid booking arrangements files based on the provided parameters.

    This method determines the valid booking arrangements file(s) for a given revision,
    service code, line name, and list of valid files. It considers various factors such
    as the number of valid files, the most recent modification datetime, and the operating
    period start date to determine the appropriate booking arrangements file(s) to return.

    Parameters:
        revision_id (int): The ID of the revision.
        valid_files (list): A list of valid files containing information about each file,
            including the filename, start date, and end date.
        service_code (str): The service code.
        line_name (str): The name of the line.

    Returns:
        QuerySet or None:
    """
    if len(valid_files) == 1:
        return get_single_booking_arrangements_file(revision_id, service_code)
    elif len(valid_files) > 1:
        booking_arrangements_qs = None
        most_recent_modification_datetime = get_most_recent_modification_datetime(
            revision_id, service_code, line_name
        )
        booking_arrangements_qs = TXCFileAttributes.objects.filter(
            revision_id=revision_id,
            service_code=service_code,
            line_names__contains=[line_name],
            modification_datetime=most_recent_modification_datetime,
        )

        if len(booking_arrangements_qs) == 1:
            return get_single_booking_arrangements_file(
                booking_arrangements_qs.first().revision_id, [service_code]
            )

        lastest_operating_period_start = get_lastest_operating_period_start_date(
            revision_id,
            service_code,
            line_name,
            most_recent_modification_datetime,
        )
        booking_arrangements_qs = booking_arrangements_qs.filter(
            operating_period_start_date=lastest_operating_period_start
        )

        if len(booking_arrangements_qs) == 1:
            return get_single_booking_arrangements_file(
                booking_arrangements_qs.first().revision_id, [service_code]
            )

        booking_arrangements_qs = booking_arrangements_qs.order_by("-filename").first()

        return get_single_booking_arrangements_file(
            booking_arrangements_qs.revision_id, [service_code]
        )
