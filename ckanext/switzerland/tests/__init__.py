import logging

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.tests import helpers

log = logging.getLogger(__name__)


class OgdchFunctionalTestBase(helpers.FunctionalTestBase):
    org = None
    dataset_dict = None
    dataset = None

    def _get_context(self):
        # We need a fresh context every time we create a dataset
        user = tk.get_action("get_site_user")({"ignore_auth": True})["name"]
        return {
            "model": model,
            "session": model.Session,
            "user": user,
            "ignore_auth": True,
        }

    @classmethod
    def teardown_class(cls):
        super(OgdchFunctionalTestBase, cls).teardown_class()
        helpers.reset_db()

    def setup(self):
        super(OgdchFunctionalTestBase, self).setup()

        # create an org
        self.org = {
            "name": "test-org",
            "title": {
                "de": "Test Org DE",
                "fr": "Test Org FR",
                "it": "Test Org IT",
                "en": "Test Org EN",
            },
            "political_level": "confederation",
        }
        tk.get_action("organization_create")(self._get_context(), self.org)

        # create a valid DCAT-AP Switzerland compliant dataset
        self.dataset_dict = {
            "coverage": "",
            "issued": "08.09.2015",
            "contact_points": [{"email": "pierre@bar.ch", "name": "Pierre"}],
            "keywords": {"fr": [], "de": [], "en": [], "it": []},
            "spatial": "",
            "publisher": {
                "name": "Bundesarchiv",
                "url": "https//opendata.swiss/organization/bundesarchiv",
            },
            "description": {
                "fr": "Description FR",
                "de": "Beschreibung DE",
                "en": "Description EN",
                "it": "Description IT",
            },
            "title": {
                "fr": "FR Test",
                "de": "DE Test",
                "en": "EN Test",
                "it": "IT Test",
            },
            "language": ["en", "de"],
            "name": "test-dataset",
            "relations": [],
            "see_alsos": [],
            "temporals": [],
            "accrual_periodicity": "http://publications.europa.eu/resource/authority/frequency/IRREG",
            "modified": "09.09.2015",
            "url": "http://some_url",
            "owner_org": "test-org",
            "identifier": "test@test-org",
        }
        self.dataset = tk.get_action("package_create")(
            self._get_context(), self.dataset_dict
        )
