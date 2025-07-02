import logging
from datetime import datetime

import ckan.plugins.toolkit as tk
import isodate
from ckan.lib.formatters import localised_nice_date
from dateutil.parser import ParserError, parse

DATE_PICKER_FORMAT = tk.config.get("ckanext.switzerland.date_picker_format", "%d.%m.%Y")
ALLOWED_DATE_FORMATS = ["%d.%m.%y"]

log = logging.getLogger(__name__)

INVALID_EMPTY_DATE = "False"
VALID_EMPTY_DATE = ""
ACCEPTED_EMPTY_DATE_VALUES = [INVALID_EMPTY_DATE, VALID_EMPTY_DATE]


def display_if_isodate(value):
    """If the value is already in isoformat, return it as-is."""
    try:
        dt = isodate.parse_datetime(value)
        if isinstance(dt, datetime):
            return value
    except Exception:
        log.debug(f"Datetime {value} is not an isoformat date")
        return None


def display_if_date_picker_date(value):
    """If the value is in ckanext.switzerland.date_picker_format, return it
    as an isoformat date.
    """
    try:
        dt = datetime.strptime(value, DATE_PICKER_FORMAT)
        if isinstance(dt, datetime):
            return dt.isoformat()
    except Exception:
        log.debug(f"Datetime {value} does not match the format {DATE_PICKER_FORMAT}")
        return None


def display_if_timestamp(value):
    """If the value is a POSIX timestamp, return it as an isoformat date."""
    try:
        dt = datetime.fromtimestamp(int(value))
        if isinstance(dt, datetime):
            return dt.isoformat()
    except Exception:
        log.debug(f"Datetime {value} is not a POSIX timestamp")
        return None


def display_if_datetime(value):
    """If the value is in a datetime object, return it as an isoformat date."""
    try:
        if isinstance(value, datetime):
            return value.isoformat()
    except Exception:
        log.debug(f"Datetime {value} is not a datetime object")
        return None


def display_if_other_formats(value):
    """If the value is another recognised date format, return it as an
    isoformat date.
    """
    for date_format in ALLOWED_DATE_FORMATS:
        try:
            dt = datetime.strptime(value, date_format)
            if isinstance(dt, datetime):
                return dt.isoformat()
        except Exception:
            log.debug(f"Datetime {value} does not match the format {date_format}")
    return None


display_date_helpers = [
    display_if_isodate,
    display_if_date_picker_date,
    display_if_timestamp,
    display_if_datetime,
    display_if_other_formats,
]


def transform_any_date_to_isodate(value):
    """Transform any stored date format into an isodate."""
    for date_helper in display_date_helpers:
        storage_date = date_helper(value)
        if storage_date:
            return storage_date


def get_latest_isodate(resource_dates):
    """return the latest date of a list of resource dates:
    the dates are all transformed into isodates,
    then a stringcomparison will bring back the
    latest of those dates
    """
    if not resource_dates:
        return ""
    isodates = [
        transform_any_date_to_isodate(date_field) for date_field in resource_dates
    ]
    latest_isodate = max(isodates)
    return latest_isodate


def correct_invalid_empty_date(value):
    """date values stored in postgres as not set"""
    if value == INVALID_EMPTY_DATE:
        log.error(
            f"Invalid date {INVALID_EMPTY_DATE} detected in database. "
            f"Date was transformed into {VALID_EMPTY_DATE}"
        )
        return VALID_EMPTY_DATE


class OGDCHDateValidationException(Exception):
    pass


def transform_date_for_solr(date):
    """Since Solr can only handle dates as isodates with UTC
    all isodates that are indexed by Solr are transformed in the
    following way:

    - timezone information is ignored
    - Z is added at the end of the isodate

    Example:
    an isodate such as 2022-10-25T15:30:10.330000+02:00 that
    comes in through harvesting is transformed into
    2022-10-25T15:30:10.33Z ignoring the timezone information, but it
    will still be stored in the original isoformat with timezone
    information in postgres
    """
    # Necessary as we still have some badly-formatted dates in the database:
    # some are the string 'False', and some are timestamps.
    if date in ACCEPTED_EMPTY_DATE_VALUES:
        return VALID_EMPTY_DATE
    date = transform_any_date_to_isodate(date)

    try:
        datetime_without_tz = parse(date, ignoretz=True)
        isodate_without_tz = isodate.datetime_isoformat(datetime_without_tz)
        return f"{isodate_without_tz}Z"
    except Exception as e:
        log.error(f"Exception {e} occured on date transformation of {date}")
        return None


def get_localized_date(value):
    """Take an isoformat date and return a localized date, e.g.
    '24. Juni 2020'.
    """
    try:
        dt = isodate.parse_datetime(str(value))
        if isinstance(dt, datetime):
            return localised_nice_date(dt, show_date=True, with_hours=False)
    except (AttributeError, ParserError, TypeError, ValueError) as e:
        log.debug(
            f"Error parsing datetime {value} as isodate and returning localized date: "
            f"{e}"
        )
        return ""


def get_date_picker_format(value):
    """Take an isoformat date and return a date in the date-picker format,
    e.g. '24.06.2020'.
    """
    try:
        dt = isodate.parse_datetime(value)
        if isinstance(dt, datetime):
            return isodate.strftime(dt, DATE_PICKER_FORMAT)
    except (AttributeError, ParserError, TypeError, ValueError) as e:
        log.debug(
            f"Error parsing datetime {value} as isodate and converting to format "
            f"{DATE_PICKER_FORMAT}: {e}"
        )
        return ""
