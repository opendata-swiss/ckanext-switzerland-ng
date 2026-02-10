"""utils used for requests"""

import ckan.plugins.toolkit as tk


def get_current_language():
    """If we are in a request context, get the request language
    Otherwise, fall back to the default language, or English.
    """
    try:
        return tk.request.environ.get(
            "CKAN_LANG", tk.config.get("ckan.locale_default", "en")
        )
    except (KeyError, RuntimeError, TypeError, AttributeError):
        return tk.config.get("ckan.locale_default", "en")


def request_is_api_request():
    try:
        # Do not change the resulting dict for API requests
        path = tk.request.path
        if any(
            [
                path.endswith(".xml"),
                path.endswith(".rdf"),
                path.endswith(".n3"),
                path.endswith(".ttl"),
                path.endswith(".jsonld"),
            ]
        ):
            return True
        if path.startswith("/api") and not path.startswith("/api/action"):
            # The API client for CKAN's JS modules uses a path starting
            # /api/action, i.e. without a version number. All other API calls
            # should include a version number.
            return True
    except (RuntimeError, TypeError):
        # we get here if there is no request (i.e. on the command line)
        return False
