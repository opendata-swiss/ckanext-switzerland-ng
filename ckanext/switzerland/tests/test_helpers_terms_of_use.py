# -*- coding: utf-8 -*-
"""Tests for helpers.py."""
from nose.tools import *  # noqa
import ckanext.switzerland.helpers.terms_of_use_utils as ogdch_term_utils
import unittest


class TestHelpers(unittest.TestCase):
    def test_get_resource_terms_of_use_with_license(self):
        term_id = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired'
        resource = {
            "license": term_id
        }
        result = ogdch_term_utils.get_resource_terms_of_use(resource)
        self.assertEquals(term_id, result)

    def test_get_resource_terms_of_use_with_rights(self):
        term_id = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired'
        resource = {
            "rights": term_id
        }
        result = ogdch_term_utils.get_resource_terms_of_use(resource)
        self.assertEquals(term_id, result)

    def test_get_resource_terms_of_use_with_license_and_rights(self):
        license_term_id = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired'
        rights_term_id = 'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired'
        resource = {
            "license": license_term_id,
            "rights": rights_term_id
        }
        result = ogdch_term_utils.get_resource_terms_of_use(resource)
        self.assertEquals(license_term_id, result)

    def test_get_resource_terms_of_use_closed(self):
        term_id = 'NonCommercialNotAllowed-CommercialAllowed-ReferenceNotRequired'  # noqa
        resource = {}
        result = ogdch_term_utils.get_resource_terms_of_use(resource)
        self.assertEquals('ClosedData', result)
