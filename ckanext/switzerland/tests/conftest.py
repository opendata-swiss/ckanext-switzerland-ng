import logging
from copy import copy

import ckan.model as model
import ckan.plugins.toolkit as tk
import pytest
from ckan.tests import factories, helpers

from ckanext.switzerland.plugins import HARVEST_USER, MIGRATION_USER

log = logging.getLogger(__name__)

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


def get_context():
    # We need a fresh context every time we create a dataset
    user = tk.get_action("get_site_user")({"ignore_auth": True})["name"]
    return {
        "model": model,
        "session": model.Session,
        "user": user,
        "ignore_auth": True,
    }


@pytest.fixture
def clean_db_and_migrate_for_ogdch_subscribe(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("ogdch_subscribe")
    migrate_db_for("activity")


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
    return tk.get_action("organization_create")(get_context(), org_dict)


@pytest.fixture
def dataset(org):
    return tk.get_action("package_create")(get_context(), dataset_dict)


@pytest.fixture
def site_user():
    return get_context()["user"]


@pytest.fixture
def users():
    for n in range(3):
        user = {
            "name": f"user{str(n)}",
            "email": f"user{str(n)}@example.org",
            "password": f"password{str(n)}",
        }
        tk.get_action("user_create")(get_context(), user)

    return tk.get_action("user_list")(get_context(), {"all_fields": False})


@pytest.fixture
def sysadmin_headers():
    user = factories.SysadminWithToken()
    headers = {"Authorization": user["token"]}
    return headers


@pytest.fixture
def no_notification_users():
    tk.get_action("user_create")(
        get_context(),
        {
            "name": HARVEST_USER,
            "email": f"{HARVEST_USER}@example.org",
            "password": f"password{HARVEST_USER}",
        },
    )
    tk.get_action("user_create")(
        get_context(),
        {
            "name": MIGRATION_USER,
            "email": f"{MIGRATION_USER}@example.org",
            "password": f"password{MIGRATION_USER}",
        },
    )


@pytest.fixture
def groups():
    groups = []
    group1 = {
        "name": "group1",
        "title": {
            "de": "Group 1 DE",
            "fr": "Group 1 FR",
            "it": "Group 1 IT",
            "en": "Group 1 EN",
        },
    }
    groups.append(tk.get_action("group_create")(get_context(), group1))

    group2 = {
        "name": "group2",
        "title": {
            "de": "Group 2 DE",
            "fr": "Group 2 FR",
            "it": "Group 2 IT",
            "en": "Group 2 EN",
        },
    }
    groups.append(tk.get_action("group_create")(get_context(), group2))

    return groups


@pytest.fixture
def extra_datasets(groups):
    extra_datasets = []

    dataset_dict_2 = copy(dataset_dict)
    dataset_dict_2["name"] = "dataset2"
    dataset_dict_2["identifier"] = "dataset2@test-org"
    dataset_dict_2["description"] = {
        "fr": "Frog FR",
        "de": "Frog DE",
        "en": "Frog EN",
        "it": "Frog IT",
    }
    extra_datasets.append(
        tk.get_action("package_create")(get_context(), dataset_dict_2)
    )

    dataset_dict_3 = copy(dataset_dict)
    dataset_dict_3["name"] = "dataset3"
    dataset_dict_3["identifier"] = "dataset3@test-org"
    dataset_dict_3["description"] = {
        "fr": "Bamboo FR",
        "de": "Bamboo DE",
        "en": "Bamboo EN",
        "it": "Bamboo IT",
    }
    dataset_dict_3["groups"] = [{"name": "group1"}]

    extra_datasets.append(
        tk.get_action("package_create")(get_context(), dataset_dict_3)
    )

    dataset_dict_4 = copy(dataset_dict)
    dataset_dict_4["name"] = "dataset4"
    dataset_dict_4["identifier"] = "dataset4@test-org"
    dataset_dict_4["description"] = {
        "fr": "Bamboo Frog FR",
        "de": "Bamboo Frog DE",
        "en": "Bamboo Frog EN",
        "it": "Bamboo Frog IT",
    }
    dataset_dict_4["groups"] = [{"name": "group2"}]

    extra_datasets.append(
        tk.get_action("package_create")(get_context(), dataset_dict_4)
    )

    return extra_datasets
