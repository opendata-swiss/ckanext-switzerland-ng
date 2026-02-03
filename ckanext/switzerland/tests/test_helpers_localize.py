import unittest

import ckanext.switzerland.helpers.localize_utils as ogdch_localize_utils

organization_title = '{"fr": "Swisstopo FR", "de": "Swisstopo DE", "en": "Swisstopo EN", "it": "Swisstopo IT"}'


class TestHelpers(unittest.TestCase):
    def test_get_localized_value_from_dict(self):
        lang_dict = {
            "de": "DE value",
            "fr": "FR value",
            "it": "IT value",
            "en": "EN value",
        }
        result = ogdch_localize_utils.get_localized_value_from_dict(lang_dict, "de")
        self.assertEqual(lang_dict["de"], result)

    def test_get_localized_value_from_dict_fallback(self):
        lang_dict = {
            "de": "DE value",
            "fr": "FR value",
            "it": "IT value",
            "en": "",
        }
        result = ogdch_localize_utils.get_localized_value_from_dict(lang_dict, "en")
        # if en does not exist, fallback to de
        self.assertEqual(lang_dict["de"], result)

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
