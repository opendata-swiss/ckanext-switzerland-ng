# -*- coding: utf-8 -*-
"""Tests for terms_of_use_utils.py."""
import unittest

from nose.tools import assert_equals

import ckanext.switzerland.helpers.terms_of_use_utils as ogdch_term_utils


class TestHelpers(object):
    def test_get_resource_terms_of_use_with_license(self):
        term_id = "https://opendata.swiss/terms-of-use#terms_by"
        resource = {"license": term_id}
        result = ogdch_term_utils.get_resource_terms_of_use(resource)
        assert_equals(term_id, result)

    def test_get_resource_terms_of_use_with_rights(self):
        term_id = "https://opendata.swiss/terms-of-use#terms_by"
        resource = {"rights": term_id}
        result = ogdch_term_utils.get_resource_terms_of_use(resource)
        assert_equals(term_id, result)

    def test_get_resource_terms_of_use_with_license_and_rights(self):
        license_term_id = "https://opendata.swiss/terms-of-use#terms_by"
        rights_term_id = "https://opendata.swiss/terms-of-use#terms_ask"
        resource = {"license": license_term_id, "rights": rights_term_id}
        result = ogdch_term_utils.get_resource_terms_of_use(resource)
        assert_equals(license_term_id, result)

    def test_get_resource_terms_of_use_closed(self):
        term_id = "NonCommercialNotAllowed-CommercialAllowed-ReferenceNotRequired"
        resource = {}
        result = ogdch_term_utils.get_resource_terms_of_use(resource)
        assert_equals("ClosedData", result)

    def test_get_dataset_terms_of_use(self):
        test_data = [
            [
                {
                    "resources": [
                        {"license": ogdch_term_utils.TERMS_OF_USE_BY},
                        {"license": ogdch_term_utils.TERMS_OF_USE_OPEN},
                    ]
                },
                ogdch_term_utils.TERMS_OF_USE_BY,
            ],
            [
                {
                    "resources": [
                        {"rights": ogdch_term_utils.TERMS_OF_USE_OPEN},
                        {"rights": ogdch_term_utils.TERMS_OF_USE_BY},
                    ]
                },
                ogdch_term_utils.TERMS_OF_USE_BY,
            ],
            [
                {
                    "resources": [
                        {"rights": ogdch_term_utils.TERMS_OF_USE_BY},
                        {"license": ogdch_term_utils.TERMS_OF_USE_OPEN},
                    ]
                },
                ogdch_term_utils.TERMS_OF_USE_BY,
            ],
            [
                {
                    "resources": [
                        {"license": ogdch_term_utils.TERMS_OF_USE_OPEN},
                        {"license": ogdch_term_utils.TERMS_OF_USE_BY},
                        {"rights": ogdch_term_utils.TERMS_OF_USE_ASK},
                        {"rights": ogdch_term_utils.TERMS_OF_USE_BY_ASK},
                    ]
                },
                ogdch_term_utils.TERMS_OF_USE_BY_ASK,
            ],
            [
                {
                    "resources": [
                        {"license": "A very cool open license"},
                        {"license": ogdch_term_utils.TERMS_OF_USE_ASK},
                    ]
                },
                ogdch_term_utils.TERMS_OF_USE_CLOSED,
            ],
            [
                {
                    "resources": [
                        {"license": "A very cool open license"},
                        {"rights": "A very cool set of rights"},
                    ]
                },
                ogdch_term_utils.TERMS_OF_USE_CLOSED,
            ],
            [
                {
                    "resources": [
                        {
                            "license": "A very cool open license",
                            "rights": ogdch_term_utils.TERMS_OF_USE_BY,
                        },
                        {
                            "license": ogdch_term_utils.TERMS_OF_USE_OPEN,
                            "rights": "A very cool set of rights",
                        },
                    ]
                },
                ogdch_term_utils.TERMS_OF_USE_BY,
            ],
            [
                {
                    "resources": [
                        {
                            # If a resource's license is in the open terms,
                            # we ignore the resource's rights statement.
                            "license": ogdch_term_utils.TERMS_OF_USE_OPEN,
                            "rights": "Rights statement not in OPEN_TERMS",
                        }
                    ]
                },
                ogdch_term_utils.TERMS_OF_USE_OPEN,
            ],
            [
                {
                    "resources": [
                        {
                            # If a resource's license is not in the open terms,
                            # we check the resource's rights statement.
                            "license": "License not in OPEN_TERMS",
                            "rights": ogdch_term_utils.TERMS_OF_USE_OPEN,
                        }
                    ]
                },
                ogdch_term_utils.TERMS_OF_USE_OPEN,
            ],
        ]

        for data in test_data:
            yield self.check_dataset_terms_of_use_are_correct, data[0], data[1]

    def check_dataset_terms_of_use_are_correct(self, dataset, expected_terms):
        assert_equals(
            ogdch_term_utils.get_dataset_terms_of_use(dataset), expected_terms
        )
