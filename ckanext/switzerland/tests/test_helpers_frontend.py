# -*- coding: utf-8 -*-
"""Tests for helpers.py."""
import unittest
from copy import deepcopy

import mock
from nose.tools import *

import ckanext.switzerland.helpers.frontend_helpers as ogdch_frontend_helpers

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


class TestHelpers(unittest.TestCase):

    @mock.patch("ckan.lib.i18n.get_lang", return_value="fr")
    def test_get_sorted_orgs_by_translated_title_fr(self, mock_get_lang):
        french_organizations = deepcopy(organizations)
        result_orgs = ogdch_frontend_helpers.get_sorted_orgs_by_translated_title(
            french_organizations
        )

        for org in result_orgs:
            if org["children"]:
                self.assertEqual(
                    0, self.find_position_of_org(org["children"], "AAAAA (FR)")
                )
                self.assertEqual(
                    1, self.find_position_of_org(org["children"], "YYYYY (FR)")
                )

        self.assertEqual(0, self.find_position_of_org(result_orgs, "AAAAA (FR)"))
        self.assertEqual(2, self.find_position_of_org(result_orgs, "YYYYY (FR)"))

    @mock.patch("ckan.lib.i18n.get_lang", return_value="it")
    def test_get_sorted_orgs_by_translated_title_it(self, mock_get_lang):
        italian_organizations = deepcopy(organizations)
        result_orgs = ogdch_frontend_helpers.get_sorted_orgs_by_translated_title(
            italian_organizations
        )

        for org in result_orgs:
            if org["children"]:
                self.assertEqual(
                    0, self.find_position_of_org(org["children"], "BBBBB (IT)")
                )
                self.assertEqual(
                    1, self.find_position_of_org(org["children"], "ZZZZZ (IT)")
                )

        self.assertEqual(2, self.find_position_of_org(result_orgs, "ZZZZZ (IT)"))
        self.assertEqual(0, self.find_position_of_org(result_orgs, "AAAAA (IT)"))

    @mock.patch("ckan.lib.i18n.get_lang", return_value="de")
    def test_get_sorted_orgs_by_translated_title_de(self, mock_get_lang):
        german_organizations = deepcopy(organizations)
        result_orgs = ogdch_frontend_helpers.get_sorted_orgs_by_translated_title(
            german_organizations
        )

        for org in result_orgs:
            if org["children"]:
                self.assertEqual(
                    0, self.find_position_of_org(org["children"], "BBBBB (DE)")
                )
                self.assertEqual(
                    1, self.find_position_of_org(org["children"], "yyyyy (DE)")
                )

        self.assertEqual(0, self.find_position_of_org(result_orgs, "bbbbb (DE)"))
        self.assertEqual(2, self.find_position_of_org(result_orgs, "ZZZZZ (DE)"))

    @mock.patch("ckan.lib.i18n.get_lang", return_value="en")
    def test_get_sorted_orgs_by_translated_title_en(self, mock_get_lang):
        english_organizations = deepcopy(organizations)
        result_orgs = ogdch_frontend_helpers.get_sorted_orgs_by_translated_title(
            english_organizations
        )

        for org in result_orgs:
            if org["children"]:
                self.assertEqual(
                    0, self.find_position_of_org(org["children"], "ööööö (EN)")
                )
                self.assertEqual(
                    1, self.find_position_of_org(org["children"], "zzzzz (EN)")
                )

        self.assertEqual(0, self.find_position_of_org(result_orgs, "ààààà (EN)"))
        self.assertEqual(1, self.find_position_of_org(result_orgs, "ÉÉÉÉÉ (EN)"))
        self.assertEqual(2, self.find_position_of_org(result_orgs, "üüüüü (EN)"))

    def find_position_of_org(self, org_list, title):
        index = next((i for i, org in enumerate(org_list) if org["title"] == title), -1)
        return index
