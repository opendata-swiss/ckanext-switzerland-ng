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
        if not author_email:
            raise ValueError("Email is missing")
        now = datetime.now()
        api_calls_per_time_and_email.append((author_email, datetime.now()))
        for (m, t) in api_calls_per_time_and_email:
            if (t + limit_timedelta < now):
                api_calls_per_time_and_email.remove((m, t))
        if len([(m, t)
                for (m, t) in api_calls_per_time_and_email
                if m == author_email]) > limit_call_count:
            log.error("rate limit exceeded for {}".format(author_email))
            context['ratelimit_exceeded'] = True
        return func(context, data_dict)
    limit_timedelta, limit_call_count = _get_limits_from_config()
    api_calls_per_time_and_email = []
    return inner


def _get_limits_from_config():
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
