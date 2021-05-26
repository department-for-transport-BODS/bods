import math
from datetime import datetime, timedelta

from django.utils import timezone


def get_simulated_progress(start_time: datetime, max_minutes: timedelta):
    """Calculates a simulated progress value.
    Assumes that a task will take `max_minutes` minutes to complete.
    """
    elapsed_time = timezone.now() - start_time
    progress = math.floor(100 * elapsed_time / max_minutes)
    progress = min(progress, 99)
    return progress
