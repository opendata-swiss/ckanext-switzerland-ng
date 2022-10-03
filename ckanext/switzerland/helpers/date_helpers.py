from datetime import datetime
import logging
import isodate
import ckan.plugins.toolkit as tk

DATE_FORMAT = tk.config.get(
    'ckanext.switzerland.date_picker_format', '%d.%m.%Y')

log = logging.getLogger(__name__)

INVALID_EMPTY_DATE = 'False'
VALID_EMPTY_DATE = ''
ACCEPTED_EMPTY_DATE_VALUES = [INVALID_EMPTY_DATE, VALID_EMPTY_DATE]


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


def transform_any_date_to_isodate(date_field):
    isodate_field = store_if_ogdch_date(date_field)
    if isodate_field:
        return isodate_field
    isodate_field = store_if_isodate(date_field)
    if isodate_field:
        return isodate_field
    isodate_field = store_if_timestamp(date_field)
    if isodate_field:
        return isodate_field


def get_latest_isodate(resource_dates):
    """return the latest date of a list of isodates"""
    if not resource_dates:
        return ''
    isodates = [transform_any_date_to_isodate(date_field) for date_field in resource_dates]
    latest_isoodate = max(isodates)
    return latest_isoodate


def correct_invalid_empty_date(value):
    """date values stored in postgres as not set"""
    if value == INVALID_EMPTY_DATE:
        log.error("Invalid date {} detected in database."
                  "Date was transformed into {}"
                  .format(INVALID_EMPTY_DATE, VALID_EMPTY_DATE))
        return VALID_EMPTY_DATE


class OGDCHDateValidationException(Exception):
    pass
