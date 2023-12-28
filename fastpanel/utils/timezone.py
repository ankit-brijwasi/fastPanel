from datetime import datetime
from typing import Union

import pytz

from ..conf import settings


def now():
    """
    Returns a timezone aware datetime object
    """
    tz = getattr(pytz, settings.TIMEZONE, "UTC")
    return datetime.now(tz)


def make_aware(date: Union[datetime, int]):
    """
    Adds timezone to a naive datetime object
    """
    if isinstance(date, int):
        date = datetime.fromtimestamp(date)

    timezone = getattr(pytz, settings.TIMEZONE, "UTC")
    return date.replace(tzinfo=timezone)


def add_system_tz(date: datetime):
    """
    Generates a new datetime object with the system's
    timezone
    """
    timezone = getattr(pytz, settings.TIMEZONE, "UTC")
    return date.astimezone(tz=timezone)

