# encoding: utf-8
import json

from ckan.lib.navl.dictization_functions import Invalid
from ckan.plugins.toolkit import get_validator
from nose.tools import assert_equals, assert_raises


class TestOgdchUrlListValidator(object):
    def setup(self):
        # We pass in dummy values for field and schema here, because we just
        # want to get the inner validation function, and that does not use
        # either of these parameters.
        self.validator = get_validator("ogdch_validate_list_of_urls")(
            'field', {}
        )

    def test_validate_url_list_string(self):
        value = '["https://example.com/1", "http://example.com/2"]'
        key = "documentation"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals(value, data[key])
        assert_equals([], errors[key])

    def test_validate_url_list_string_with_invalid_url(self):
        value = '["http://example.com/foo", "foobar"]'
        key = "documentation"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals(value, data[key])
        assert_equals([u"Provided URL 'foobar' is not valid"], errors[key])
