from datetime import datetime

from dateutil import tz
from dateutil.parser import parse


def extract_timestamp(timestamp: str, default: datetime = None, *args, **kwargs):
    try:
        ts = parse(timestamp, *args, **kwargs)
        if not ts.tzinfo:
            # Timezone information is missing
            ts = ts.replace(tzinfo=tz.gettz("Europe/London"))
        return ts
    except (TypeError, ValueError):
        return default
