# encoding: utf-8
import json

from ckan.lib.navl.dictization_functions import Invalid
from ckan.plugins.toolkit import get_validator
from nose.tools import assert_equals, assert_raises, assert_true, assert_false


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


class TestOgdchUrlValidator(object):
    def setUp(self):
        self.validator = get_validator("ogdch_validate_url",
                                       {'field': None, 'schema': {}})

    def test_valid_http_url(self):
        data = {"my_url": "http://www.example.com"}
        result = self.validator("my_url", data, {}, None)
        assert_true(result)

    def test_valid_https_url(self):
        data = {"my_url": "https://www.example.com"}
        result = self.validator("my_url", data, {}, None)
        assert_true(result)

    def test_invalid_url(self):
        data = {"my_url": "not_a_url"}
        result = self.validator("my_url", data, {}, None)
        assert_false(result)

    def test_url_not_accessible(self):
        data = {"my_url": "http://nonexistenturl12345.com"}
        result = self.validator("my_url", data, {}, None)
        assert_false(result)