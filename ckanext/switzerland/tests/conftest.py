import logging

import ckan.model as model
import ckan.plugins.toolkit as tk
import pytest
from ckan.tests import helpers

log = logging.getLogger(__name__)


def _get_context():
    # We need a fresh context every time we create a dataset
    user = tk.get_action("get_site_user")({"ignore_auth": True})["name"]
    return {
        "model": model,
        "session": model.Session,
        "user": user,
        "ignore_auth": True,
    }


@pytest.fixture
def org():
    org_dict = {
        "name": "test-org",
        "title": {
            "de": "Test Org DE",
            "fr": "Test Org FR",
            "it": "Test Org IT",
            "en": "Test Org EN",
        },
        "political_level": "confederation",
    }
    return tk.get_action("organization_create")(_get_context(), org_dict)


@pytest.fixture
def dataset(org):
    dataset_dict = {
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

    return tk.get_action("package_create")(_get_context(), dataset_dict)
