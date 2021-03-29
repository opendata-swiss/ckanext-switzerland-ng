# -*- coding: utf-8 -*-
"""Tests for helpers.py."""
from nose.tools import *  # noqa
import ckanext.switzerland.helpers.terms_of_use_utils as ogdch_term_utils
import unittest


class TestHelpers(unittest.TestCase):
    def test_simplify_terms_of_use_open(self):
        term_id = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired'
        result = ogdch_term_utils.simplify_terms_of_use(term_id)
        self.assertEquals(term_id, result)

    def test_simplify_terms_of_use_closed(self):
        term_id = 'NonCommercialNotAllowed-CommercialAllowed-ReferenceNotRequired'  # noqa
        result = ogdch_term_utils.simplify_terms_of_use(term_id)
        self.assertEquals('ClosedData', result)
