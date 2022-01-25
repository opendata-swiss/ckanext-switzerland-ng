from datetime import datetime
import logging
from dateutil.parser import parse
import ckan.plugins.toolkit as tk

DATE_FORMAT = tk.config.get(
    'ckanext.switzerland.date_picker_format', '%d.%m.%Y')

log = logging.getLogger(__name__)


def get_isodate_as_isodate(value):
    try:
        value_as_isoformat = parse(value).isoformat()
        if value_as_isoformat == value:
            return value
    except Exception:
        return None


def get_ogdch_date_as_isodate(value):
    try:
        return datetime.strptime(value, DATE_FORMAT).isoformat()
    except Exception:
        return None


def get_timestamp_date_as_isodate(value):
    try:
        return datetime.fromtimestamp(int(value)).isoformat()
    except Exception:
        return None


def get_datetime_date_as_isodate(value):
    try:
        return value.isoformat()
    except Exception:
        return None


def get_ogdch_date_from_isodate(value):
    try:
        value_as_isoformat = parse(value).isoformat()
        if value_as_isoformat == value:
            return parse(value).strftime(DATE_FORMAT)
    except Exception:
        return None


def get_ogdch_date_from_ogdch_date(value):
    try:
        datetime_derived_from_value_by_format = datetime.strptime(value, DATE_FORMAT)
        if datetime_derived_from_value_by_format:
            return value
    except Exception:
        return None


def get_ogdch_date_from_timestamp(value):
    try:
        value_as_datetime = datetime.fromtimestamp(int(value))
        return value_as_datetime.strftime(DATE_FORMAT)
    except Exception:
        return None


def get_ogdch_date_from_datetime(value):
    try:
        return value.strftime(DATE_FORMAT)
    except Exception:
        return None
