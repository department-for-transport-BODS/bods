import math
from datetime import datetime, timedelta

from django.utils import timezone
from transit_odp.organisation.models import TXCFileAttributes


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
        noc_dict = txc_attributes.setdefault(
            file_attribute.licence_number, {}
        ).setdefault(file_attribute.national_operator_code, {})
        line_names_dict = noc_dict.setdefault(file_attribute.line_names[0], set())

        line_names_dict.add(file_attribute.service_code)

    return txc_attributes
