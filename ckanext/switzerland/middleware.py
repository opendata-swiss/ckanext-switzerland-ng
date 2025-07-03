import logging

log = logging.getLogger(__name__)


class RobotsHeaderMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        def new_start_response(status, response_headers, exc_info=None):
            """Add noindex, nofollow header to all responses."""
            response_headers.append(("X-Robots-Tag", "noindex, nofollow"))

            return start_response(status, response_headers, exc_info)

        return self.app(environ, new_start_response)
