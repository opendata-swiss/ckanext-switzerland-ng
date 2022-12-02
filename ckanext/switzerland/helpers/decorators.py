from datetime import datetime, timedelta
import functools
from ckan.common import config

import logging

log = logging.getLogger(__name__)


def ratelimit(func):
    """limits the rate of calls with the same email
    Can be used for any logic function that has an author_email
    in the data_dict as mandatory field and wants to limit the
    number of calls within a given time interval.
    - the timeinterval and limit of calls can be set in the ckan config
    - in case of an exceeded limit the context is set accorfingly, so
    that the api function can react on it
    """
    @functools.wraps(func)
    def inner(context, data_dict):
        author_email = data_dict.get('author_email')
        if author_email:
            _add_new_call_and_remove_old_calls(
                api_calls_per_time_and_email,
                author_email,
                limit_timedelta,
            )
            count_of_calls_per_email = _get_call_count_for_author_email(
                api_calls_per_time_and_email,
                author_email,
            )
            if count_of_calls_per_email > limit_call_count:
                log.debug("Rate limit exceeded for {}".format(author_email))
                context['ratelimit_exceeded'] = True
                context['limit_call_count'] = limit_call_count
                context['limit_timedelta'] = limit_timedelta
                context['count_of_calls_per_email'] = count_of_calls_per_email
        return func(context, data_dict)
    limit_timedelta, limit_call_count = get_limits_from_config()
    api_calls_per_time_and_email = []
    return inner


def _add_new_call_and_remove_old_calls(api_calls_per_time_and_email,
                                       author_email,
                                       limit_timedelta):
    """
    Adds the new call for author_email and remove calls that are
    outside the considered timedelta to the list of api calls
    """
    now = datetime.now()
    this_call_tuple = (author_email, datetime.now())
    api_calls_per_time_and_email.append(this_call_tuple)
    for (m, t) in api_calls_per_time_and_email:
        tuple_expired = t + limit_timedelta < now
        if tuple_expired:
            api_calls_per_time_and_email.remove((m, t))


def _get_call_count_for_author_email(api_calls_per_time_and_email,
                                     author_email):
    """
    Checks whether the call limit for author_email is exceeded
    """
    calls_with_same_email_as_author_email = \
        [(m, t)
         for (m, t) in api_calls_per_time_and_email
         if m == author_email]
    return len(calls_with_same_email_as_author_email)


def get_limits_from_config():
    try:
        limit_timedelta = timedelta(
            seconds=int(
                config.get(
                    'ckanext.switzerland.api_limit_interval_in_seconds',
                    300)
            )
        )
    except (ValueError, TypeError):
        limit_timedelta = timedelta(minutes=5)
    try:
        limit_call_count = int(
            config.get(
                'ckanext.switzerland.api_limit_calls_per_interval',
                2
            )
        )
    except ValueError:
        limit_call_count = 2
    return limit_timedelta, limit_call_count
