# encoding: utf-8
from ckan.logic.validators import missing
from ckan.plugins.toolkit import get_validator
from nose.tools import assert_equals


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

        
class TestOgdchUriListValidator(object):
    def setUp(self):
        self.validator = get_validator("ogdch_validate_list_of_uris")(
            'field', {}
        )

    # positive tests
    def test_validate_uri_list_string(self):
        value = '["http://example.com/1", "https://example.com/2", "ftp://example.com"]'
        key = "conforms_to"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals(value, data[key])
        assert_equals([], errors[key])

    # negative tests
    def test_invalid_uri_list_string(self):
        value = '["invaliduri", "ftp://example.com"]'
        key = "conforms_to"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals(value, data[key])
        assert_equals([u"Provided URI 'invaliduri' is not valid"], errors[key])

    def test_empty_uri_list_string(self):
        value = '["", ""]'
        key = "conforms_to"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals('[]', data[key])
        assert_equals([], errors[key])


class TestOgdchLicenseRequiredValidator(object):
    def setup(self):
        self.validator = get_validator('ogdch_license_required')(
            'field', {}
        )

    def test_validate_license(self):
        value = 'Creative Commons CC Zero License (cc-zero)'
        key = (u'resources', 0, u'license')
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals(value, data[key])
        assert_equals([], errors[key])

    def test_validate_rights(self):
        value = missing
        key = (u'resources', 0, u'license')
        rights_value = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired'
        rights_key = (u'resources', 0, u'rights')

        data = {
            key: value,
            rights_key: rights_value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals(
            'NonCommercialAllowed-CommercialAllowed-ReferenceRequired',
            data[key]
        )
        assert_equals([], errors[key])

    def test_validate_both_license_and_rights(self):
        value = 'Creative Commons CC Zero License (cc-zero)'
        key = (u'resources', 0, u'license')
        rights_value = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired'
        rights_key = (u'resources', 0, u'rights')

        data = {
            key: value,
            rights_key: rights_value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals(value, data[key])
        assert_equals([], errors[key])

    def test_validate_neither_licence_nor_rights(self):
        value = missing
        key = (u'resources', 0, u'license')
        rights_value = missing
        rights_key = (u'resources', 0, u'rights')
        data = {
            key: value,
            rights_key: rights_value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals('', data[key])
        assert_equals(
            ["Distributions must have either 'rights' or 'license'"],
            errors[key]
        )
        
        
class TestOgdchDurationType(object):
    def setup(self):
        # We pass in dummy values for field and schema here, because we just
        # want to get the inner validation function, and that does not use
        # either of these parameters.
        self.validator = get_validator("ogdch_validate_duration_type")(
            'field', {}
        )

    # positive tests
    def test_valid_duration(self):
        value = "P1Y2M3DT4H5M6S"
        key = "temporal_resolution"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals(value, data[key])
        assert_equals([], errors[key])

    # negative tests
    def test_empty_value(self):
        key = "temporal_resolution"
        data = {
            key: "",
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals("", data[key])
        assert_equals([], errors[key])

    def test_missing_value(self):
        key = "temporal_resolution"
        data = {}
        errors = {
            key: [],
        }
        data[key] = {}

        self.validator(key, data, errors, {})

        assert_equals("", data[key])
        assert_equals([], errors[key])

    def test_invalid_duration(self):
        value = "InvalidDuration"
        key = "temporal_resolution"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        self.validator(key, data, errors, {})

        assert_equals("", data[key])
        assert_equals([], errors[key])