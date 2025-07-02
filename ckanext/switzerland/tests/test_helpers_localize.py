# -*- coding: utf-8 -*-
"""Tests for helpers.py."""
from nose.tools import *  # noqa

import ckanext.switzerland.helpers.localize_utils as ogdch_localize_utils
import unittest

organizations = [
    {
        "children": [],
        "highlighted": False,
        "id": "7dbaad15-597f-499c-9a72-95de38b95cad",
        "name": "swiss-library",
        "title": '{"fr": "AAAAA (FR)", "de": "bbbbb (DE)", "en": "ààààà (EN)", "it": "ZZZZZ (IT)"}',
    },  # noqa
    {
        "children": [],
        "highlighted": False,
        "id": "51941490-5ade-4d06-b708-ff04279ce550",
        "name": "italian-library",
        "title": '{"fr": "YYYYY (FR)", "de": "ZZZZZ (DE)", "en": "üüüüü (EN)", "it": "AAAAA (IT)"}',
    },  # noqa
    {
        "children": [
            {
                "children": [],
                "highlighted": False,
                "id": "589ff525-be2f-4059-bea4-75c92739dfe9",
                "name": "child-swiss-library",
                "title": '{"fr": "AAAAA (FR)", "de": "yyyyy (DE)", "en": "zzzzz (EN)", "it": "BBBBB (IT)"}',
            },  # noqa
            {
                "children": [],
                "highlighted": False,
                "id": "2c559631-e174-4e9f-8c2a-940a08371340",
                "name": "child-italian-library",
                "title": '{"fr": "YYYYY (FR)", "de": "BBBBB (DE)", "en": "ööööö (EN)", "it": "ZZZZZ (IT)"}',
            },
        ],  # noqa
        "highlighted": False,
        "id": "73124d1e-c2aa-4d20-a42d-fa71b8946e93",
        "name": "swisstopo",
        "title": '{"fr": "Swisstopo FR", "de": "Swisstopo DE", "en": "ÉÉÉÉÉ (EN)", "it": "Swisstopo IT"}',
    },
]  # noqa

organization_title = '{"fr": "Swisstopo FR", "de": "Swisstopo DE", "en": "Swisstopo EN", "it": "Swisstopo IT"}'  # noqa


class TestHelpers(unittest.TestCase):
    def test_get_localized_value_from_dict(self):
        lang_dict = {
            "de": "DE value",
            "fr": "FR value",
            "it": "IT value",
            "en": "EN value",
        }
        result = ogdch_localize_utils.get_localized_value_from_dict(lang_dict, "de")
        self.assertEquals(lang_dict["de"], result)

    def test_get_localized_value_from_dict_fallback(self):
        lang_dict = {
            "de": "DE value",
            "fr": "FR value",
            "it": "IT value",
            "en": "",
        }
        result = ogdch_localize_utils.get_localized_value_from_dict(lang_dict, "en")
        # if en does not exist, fallback to de
        self.assertEquals(lang_dict["de"], result)

    def test_parse_json_error_and_default_value(self):
        """if an error occurs the default value should be returned"""
        value = "{Hallo"
        default_value = "Hello world"
        self.assertEqual(
            ogdch_localize_utils.parse_json(value, default_value=default_value),
            default_value,
        )

    def test_parse_json_with_error(self):
        """if an error occurs the value should be returned as is"""
        value = "{Hallo"
        self.assertEqual(ogdch_localize_utils.parse_json(value), value)

    def test_parse_json_without_error(self):
        value = '{"de": "Hallo", "it": "okay"}'
        value_as_dict = {"de": "Hallo", "it": "okay"}
        self.assertEqual(ogdch_localize_utils.parse_json(value), value_as_dict)

    def test_parse_json_number_string(self):
        value = "6"
        self.assertEqual(ogdch_localize_utils.parse_json(value), value)
