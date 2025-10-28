from copy import deepcopy
from unittest.mock import patch

import pytest

import ckanext.switzerland.helpers.frontend_helpers as ogdch_frontend_helpers
import ckanext.switzerland.helpers.localize_utils as localize_utils

organizations = [
    {
        "children": [],
        "highlighted": False,
        "id": "7dbaad15-597f-499c-9a72-95de38b95cad",
        "name": "swiss-library",
        "title": '{"fr": "AAAAA (FR)", "de": "bbbbb (DE)", "en": "ààààà (EN)", "it": "ZZZZZ (IT)"}',
    },
    {
        "children": [],
        "highlighted": False,
        "id": "51941490-5ade-4d06-b708-ff04279ce550",
        "name": "italian-library",
        "title": '{"fr": "YYYYY (FR)", "de": "ZZZZZ (DE)", "en": "üüüüü (EN)", "it": "AAAAA (IT)"}',
    },
    {
        "children": [
            {
                "children": [],
                "highlighted": False,
                "id": "589ff525-be2f-4059-bea4-75c92739dfe9",
                "name": "child-swiss-library",
                "title": '{"fr": "AAAAA (FR)", "de": "yyyyy (DE)", "en": "zzzzz (EN)", "it": "BBBBB (IT)"}',
            },
            {
                "children": [],
                "highlighted": False,
                "id": "2c559631-e174-4e9f-8c2a-940a08371340",
                "name": "child-italian-library",
                "title": '{"fr": "YYYYY (FR)", "de": "BBBBB (DE)", "en": "ööööö (EN)", "it": "ZZZZZ (IT)"}',
            },
        ],
        "highlighted": False,
        "id": "73124d1e-c2aa-4d20-a42d-fa71b8946e93",
        "name": "swisstopo",
        "title": '{"fr": "Swisstopo FR", "de": "Swisstopo DE", "en": "ÉÉÉÉÉ (EN)", "it": "Swisstopo IT"}',
    },
]

organization_title = '{"fr": "Swisstopo FR", "de": "Swisstopo DE", "en": "Swisstopo EN", "it": "Swisstopo IT"}'


class TestHelpers(object):

    @patch("ckan.lib.i18n.get_lang", return_value="fr")
    def test_get_sorted_orgs_by_translated_title_fr(self, mock_get_lang):
        french_organizations = deepcopy(organizations)
        result_orgs = ogdch_frontend_helpers.get_sorted_orgs_by_translated_title(
            french_organizations
        )

        for org in result_orgs:
            if org["children"]:
                assert (0, self.find_position_of_org(org["children"], "AAAAA (FR)"))
                assert (1, self.find_position_of_org(org["children"], "YYYYY (FR)"))

        assert (0, self.find_position_of_org(result_orgs, "AAAAA (FR)"))
        assert (2, self.find_position_of_org(result_orgs, "YYYYY (FR)"))

    @patch("ckan.lib.i18n.get_lang", return_value="it")
    def test_get_sorted_orgs_by_translated_title_it(self, mock_get_lang):
        italian_organizations = deepcopy(organizations)
        result_orgs = ogdch_frontend_helpers.get_sorted_orgs_by_translated_title(
            italian_organizations
        )

        for org in result_orgs:
            if org["children"]:
                assert (0, self.find_position_of_org(org["children"], "BBBBB (IT)"))
                assert (1, self.find_position_of_org(org["children"], "ZZZZZ (IT)"))

        assert (2, self.find_position_of_org(result_orgs, "ZZZZZ (IT)"))
        assert (0, self.find_position_of_org(result_orgs, "AAAAA (IT)"))

    @patch("ckan.lib.i18n.get_lang", return_value="de")
    def test_get_sorted_orgs_by_translated_title_de(self, mock_get_lang):
        german_organizations = deepcopy(organizations)
        result_orgs = ogdch_frontend_helpers.get_sorted_orgs_by_translated_title(
            german_organizations
        )

        for org in result_orgs:
            if org["children"]:
                assert (0, self.find_position_of_org(org["children"], "BBBBB (DE)"))
                assert (1, self.find_position_of_org(org["children"], "yyyyy (DE)"))

        assert (0, self.find_position_of_org(result_orgs, "bbbbb (DE)"))
        assert (2, self.find_position_of_org(result_orgs, "ZZZZZ (DE)"))

    @patch("ckan.lib.i18n.get_lang", return_value="en")
    def test_get_sorted_orgs_by_translated_title_en(self, mock_get_lang):
        english_organizations = deepcopy(organizations)
        result_orgs = ogdch_frontend_helpers.get_sorted_orgs_by_translated_title(
            english_organizations
        )

        for org in result_orgs:
            if org["children"]:
                assert (0, self.find_position_of_org(org["children"], "ööööö (EN)"))
                assert (1, self.find_position_of_org(org["children"], "zzzzz (EN)"))

        assert (0, self.find_position_of_org(result_orgs, "ààààà (EN)"))
        assert (1, self.find_position_of_org(result_orgs, "ÉÉÉÉÉ (EN)"))
        assert (2, self.find_position_of_org(result_orgs, "üüüüü (EN)"))

    def find_position_of_org(self, org_list, title):
        index = next((i for i, org in enumerate(org_list) if org["title"] == title), -1)
        return index

    prepare_display_data = [
        ("a", {"de": "a", "en": "a", "fr": "a", "it": "a"}),
        ("1", {"de": "1", "en": "1", "fr": "1", "it": "1"}),
        ("true", {"de": "true", "en": "true", "fr": "true", "it": "true"}),
        (
            {"de": "title_de", "en": "title_en", "fr": "title_fr", "it": "title_it"},
            {"de": "title_de", "en": "title_en", "fr": "title_fr", "it": "title_it"},
        ),
        (
            '{"de": "title_de", "en": "title_en", "fr": "title_fr", "it": "title_it"}',
            {"de": "title_de", "en": "title_en", "fr": "title_fr", "it": "title_it"},
        ),
        (
            {"de": "true", "en": "false", "fr": "101", "it": "0.25"},
            {"de": "true", "en": "false", "fr": "101", "it": "0.25"},
        ),
        (
            '{"de": "true", "en": "false", "fr": "101", "it": "0.25"}',
            {"de": "true", "en": "false", "fr": "101", "it": "0.25"},
        ),
    ]

    @pytest.mark.parametrize("value, expected", prepare_display_data)
    def test_get_localized_value_for_display(self, value, expected):
        for lang in localize_utils.LANGUAGES:
            with patch(
                "ckanext.switzerland.helpers.frontend_helpers.lang", return_value=lang
            ):
                localized_value = (
                    ogdch_frontend_helpers.get_localized_value_for_display(value)
                )
                assert expected[lang] == localized_value
