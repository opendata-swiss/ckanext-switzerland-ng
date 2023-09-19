# -*- coding: utf-8 -*-
# Tests for plugin_utils.py
import logging

import unittest

import ckanext.switzerland.helpers.plugin_utils as ogdch_plugin_utils

log = logging.getLogger(__name__)


class TestPluginUtils(unittest.TestCase):
    def test_map_resource_docs_to_dataset(self):
        pkg_dict = {
            "documentation": [
                "https://example.com/documentation-dataset-1",
                "https://example.com/documentation-dataset-2"
            ],
            "resources": [
                {
                    "id": "resource-1",
                    "documentation": [
                        "https://example.com/documentation-resource-1",
                        "https://example.com/documentation-dataset-1",
                        "https://example.com/documentation-dataset-2"
                    ]
                },
                {
                    "id": "resource-2",
                    "documentation": [
                        "https://example.com/documentation-resource-2",
                        "https://example.com/documentation-dataset-1",
                        "https://example.com/documentation-dataset-2"
                    ]
                }
            ]
        }
        mapped_pkg = pkg_dict
        ogdch_plugin_utils.ogdch_map_resource_docs_to_dataset(mapped_pkg)

        # Test all documentation links are mapped onto the dataset and
        # deduplicated.
        self.assertEquals(len(mapped_pkg["documentation"]), 4)
        self.assertEquals(
            sorted(mapped_pkg["documentation"]),
            [
                "https://example.com/documentation-dataset-1",
                "https://example.com/documentation-dataset-2",
                "https://example.com/documentation-resource-1",
                "https://example.com/documentation-resource-2",
            ]
        )
        # Test resource documentation links are unchanged.
        for mapped_resource in mapped_pkg["resources"]:
            for resource in pkg_dict["resources"]:
                if mapped_resource["id"] == resource["id"]:
                    self.assertEquals(
                        sorted(mapped_resource["documentation"]),
                        sorted(resource["documentation"])
                    )
