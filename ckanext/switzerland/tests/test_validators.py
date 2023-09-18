# encoding: utf-8
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

    def test_validate_url_list(self):
        urls = ["https://example.com/1", "http://example.com/2"]
        # We pass in dummy values for field and schema here, because we just
        # want to get the inner validation function, and that does not use
        # either of these parameters.
        assert_equals(urls, self.validator(urls))

    def test_validate_url_list_string(self):
        urls = '["https://example.com/1", "http://example.com/2"]'
        assert_equals(urls, self.validator(urls))

    def test_validate_single_url(self):
        url = "http://example.com/foo"

        with assert_raises(Invalid) as cm:
            self.validator(url)

        assert_equals(
            cm.exception.error,
            "Error converting http://example.com/foo into a list: "
            "No JSON object could be decoded"
        )

    def test_validate_invalid_url(self):
        urls = ["http://example.com/foo", "foobar"]

        with assert_raises(Invalid) as cm:
            self.validator(urls)

        assert_equals(
            cm.exception.error,
            "Provided URL foobar does not have a valid schema or netloc"
        )
