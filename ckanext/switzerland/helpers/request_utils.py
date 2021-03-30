"""utils used for requests"""
import requests
import ckan.plugins.toolkit as tk


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
