import logging
from ckanext.subscribe.controller import SubscribeController

log = logging.getLogger(__name__)


class OgdchSubscribeController(SubscribeController):
    def validate_and_signup(self):
        log.warning("In OgdchSubscribeController")
        return self.signup()
