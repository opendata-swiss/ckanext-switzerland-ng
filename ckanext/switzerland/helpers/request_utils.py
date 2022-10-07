"""utils used for requests"""
import requests
import ckan.plugins.toolkit as tk
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo

FIVE_MINUTES = 300

def get_content_headers(url):
    response = requests.head(url)
    return response


def get_request_language():
    try:
        return tk.request.environ['CKAN_LANG']
    except TypeError:
        return tk.config.get('ckan.locale_default', 'en')


def request_is_api_request():
    try:
        # Do not change the resulting dict for API requests
        path = tk.request.path
        if any([
            path.endswith('.xml'),
            path.endswith('.rdf'),
            path.endswith('.n3'),
            path.endswith('.ttl'),
            path.endswith('.jsonld'),

        ]):
            return True
        if path.startswith('/api') and not path.startswith('/api/action'):
            # The API client for CKAN's JS modules uses a path starting
            # /api/action, i.e. without a version number. All other API calls
            # should include a version number.
            return True
    except TypeError:
        # we get here if there is no request (i.e. on the command line)
        return False


@on_exception(expo, RateLimitException, max_tries=8)
@limits(calls=2, period=FIVE_MINUTES)
def set_call_api_limit(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception('API response: {}'.format(response.status_code))

    return response