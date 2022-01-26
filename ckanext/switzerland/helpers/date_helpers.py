from datetime import datetime
import logging
import isodate
import ckan.plugins.toolkit as tk

DATE_FORMAT = tk.config.get(
    'ckanext.switzerland.date_picker_format', '%d.%m.%Y')

log = logging.getLogger(__name__)


def store_if_isodate(value):
    """as the storage format is isodate, isodate are just
    stored the way they come in: the function just tests whether
    the value is an isodate. In that case it is returned the way
    it is."""
    try:
        dt = isodate.parse_datetime(value)
        if isinstance(dt, datetime):
            return value
    except Exception:
        return None


def store_if_ogdch_date(value):
    """date in the ckanext.switzerland.date_picker_format will be transformed
    into isodates and stored that way."""
    try:
        dt = datetime.strptime(value, DATE_FORMAT)
        if isinstance(dt, datetime):
            return dt.isoformat()
    except Exception:
        return None


def store_if_timestamp(value):
    """timestamps will be transformed
    into isodates and stored that way."""
    try:
        dt = datetime.fromtimestamp(int(value))
        if isinstance(dt, datetime):
            return dt.isoformat()
    except Exception:
        return None


def store_if_datetime(value):
    """datetimes will be transformed
    into isodates and stored that way."""
    try:
        if isinstance(value, datetime):
            return value.isoformat()
    except Exception:
        return None


def display_if_isodate(value):
    """isodate values will be displayed in
    ckanext.switzerland.date_picker_format
    """
    try:
        dt = isodate.parse_datetime(value)
        if isinstance(dt, datetime):
            return isodate.strftime(dt, DATE_FORMAT)
    except Exception:
        return None


def display_if_ogdch_date(value):
    """since the display date format is
    the ckanext.switzerland.date_picker_format the value will
    be checked whether it is in this format. If so it
    will be returned as is."""
    try:
        dt = datetime.strptime(value, DATE_FORMAT)
        if isinstance(dt, datetime):
            return value
    except Exception:
        return None


def display_if_timestamp(value):
    """timestamps will be displayed in
    ckanext.switzerland.date_picker_format
    """
    try:
        dt = datetime.fromtimestamp(int(value))
        if isinstance(dt, datetime):
            return isodate.strftime(dt, DATE_FORMAT)
    except Exception:
        return None


def display_if_datetime(value):
    """datetime values will be displayed in
    ckanext.switzerland.date_picker_format
    """
    try:
        if isinstance(value, datetime):
            return isodate.strftime(value, DATE_FORMAT)
    except Exception:
        return None
