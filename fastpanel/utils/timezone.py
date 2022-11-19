from datetime import datetime

import pytz

from fastpanel import settings


def now():
    """
    Returns a timezone aware datetime object
    """
    tz = getattr(pytz, settings.TIMEZONE)
    return datetime.now(tz)
