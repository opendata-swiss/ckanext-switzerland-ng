from datetime import datetime
import logging
from dateutil.parser import parse
import ckan.plugins.toolkit as tk

DATE_FORMAT = tk.config.get(
    'ckanext.switzerland.date_picker_format', '%d.%m.%Y')

log = logging.getLogger(__name__)


def isodate_or_none_for_storage(value):
    try:
        value_as_isoformat = parse(value).isoformat()
        if value_as_isoformat == value:
            return value
    except Exception:
        return None


def ogdch_date_or_none_for_storage(value):
    try:
        return datetime.strptime(value, DATE_FORMAT).isoformat()
    except Exception:
        return None


def timestamp_date_or_none_for_storage(value):
    try:
        return datetime.fromtimestamp(int(value)).isoformat()
    except Exception:
        return None


def datetime_or_none_for_storage(value):
    try:
        if isinstance(value, datetime):
            return value.isoformat()
    except Exception:
        return None


def isodate_or_none_for_display(value):
    try:
        value_datetime = parse(value)
        if value_datetime.isoformat() == value:
            return get_ogdch_date(value_datetime)
    except Exception:
        return None


def ogdch_date_or_none_for_display(value):
    try:
        if datetime.strptime(value, DATE_FORMAT):
            return value
    except Exception:
        return None


def timestamp_or_none_for_display(value):
    try:
        value_datetime = datetime.fromtimestamp(int(value))
        return get_ogdch_date(value_datetime)
    except Exception:
        return None


def datetime_or_none_for_display(value):
    try:
        if isinstance(value, datetime):
            return get_ogdch_date(value)
    except Exception:
        return None


def get_ogdch_date(date_time_value):
    try:
        return date_time_value.strftime(DATE_FORMAT)
    except ValueError:
        # The date is before 1900 so we have to format it ourselves.
        # See the docs for the Python 2 time library:
        # https://docs.python.org/2.7/library/time.html
        return DATE_FORMAT.replace('%d', str(date_time_value.day).zfill(2))\
            .replace('%m', str(date_time_value.month).zfill(2))\
            .replace('%Y', str(date_time_value.year))
