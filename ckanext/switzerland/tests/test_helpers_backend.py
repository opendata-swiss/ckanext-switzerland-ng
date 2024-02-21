# -*- coding: utf-8 -*-
import ckan.plugins.toolkit as tk
import ckanext.switzerland.helpers.backend_helpers as helpers
import unittest


class TestBackendHelpers(unittest.TestCase):
    def test_get_connectome_url_ascii_identifier(self):
        tk.config["ckanext.switzerland.switch_connectome_base_url"] = \
            "https://test-connectome.ch/"
        identifier = u"12345@my-org"
        connectome_url = helpers.ogdch_get_switch_connectome_url(identifier)
        self.assertEqual(
            connectome_url,
            "https://test-connectome.ch/12345%40my-org"
        )

    def test_get_connectome_url_unicode_identifier(self):
        tk.config["ckanext.switzerland.switch_connectome_base_url"] = \
            "https://test-connectome.ch/"
        identifier = u"überwachung@my-org"
        connectome_url = helpers.ogdch_get_switch_connectome_url(identifier)
        self.assertEqual(
            connectome_url,
            "https://test-connectome.ch/%C3%BCberwachung%40my-org"
        )
