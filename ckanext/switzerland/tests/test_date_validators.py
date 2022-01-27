# encoding: utf-8

from nose.tools import assert_equals, assert_raises
from dateutil.parser import parse
from datetime import datetime

from ckan.plugins.toolkit import get_validator, Invalid


class TestOgdchDateStorageValidator(object):
    def setup(self):
        self.validator = get_validator('ogdch_date_validator')

    def test_ogdch_date_validator_parseeable_date_to_isodate(self):
        d = parse('2022-01-02')
        d_storage = d.isoformat()
        assert_equals(d_storage, self.validator(d))

    def test_ogdch_date_validator_isodate_to_isodate(self):
        d = parse('2022-01-02').isoformat()
        d_storage = d
        assert_equals(d_storage, self.validator(d))

    def test_ogdch_german_date_to_isodate(self):
        d = '02.04.2020'
        d_storage = parse(d, dayfirst=True).isoformat()
        assert_equals(d_storage, self.validator(d))

    def test_timestamp_to_isodate(self):
        date_value = parse(str('04.05.2000'), dayfirst=True)
        epoch = datetime(1970, 1, 1)
        d = int((date_value - epoch).total_seconds())
        d_storage = date_value.isoformat()
        assert_equals(d_storage, self.validator(d))

    def test_ogdch_date_validator_isodate_before_1870_to_isodate(self):
        d = parse('1655-01-02').isoformat()
        d_storage = d
        assert_equals(d_storage, self.validator(d))

    def test_ogdch_date_validator_datetime_to_isodate(self):
        d = datetime(2022, 1, 2, 0, 0)
        d_storage = d.isoformat()
        assert_equals(d_storage, self.validator(d))

    def test_ogdch_date_validator_parseeable_with_timezone_to_isodate(self):
        d = '2008-09-03T20:56:35.450686Z'
        d_storage = d
        assert_equals(d_storage, self.validator(d))


class TestOgdchDateDisplayValidator(object):
    def setup(self):
        self.validator = get_validator('ogdch_date_output')

    def test_ogdch_date_validator_parseeable_date_to_ogdch_date(self):
        d = parse('2022-01-02')
        d_display = '02.01.2022'
        assert_equals(d_display, self.validator(d))

    def test_ogdch_date_validator_isodate_to_ogdch_date(self):
        d = parse('2022-01-02').isoformat()
        d_display = '02.01.2022'
        assert_equals(d_display, self.validator(d))

    def test_ogdch_german_date_to_ogdch_date(self):
        d = '02.04.2020'
        d_display = d
        assert_equals(d_display, self.validator(d))

    def test_timestamp_to_ogdch_date(self):
        date_value = parse(str('04.05.2000'), dayfirst=True)
        epoch = datetime(1970, 1, 1)
        d = int((date_value - epoch).total_seconds())
        d_display = '04.05.2000'
        assert_equals(d_display, self.validator(d))

    def test_ogdch_date_validator_isodate_before_1870_to_ogdch_date(self):
        d = parse('1655-01-02').isoformat()
        d_display = '02.01.1655'
        assert_equals(d_display, self.validator(d))

    def test_ogdch_date_validator_datetime_to_ogdch_date(self):
        d = datetime(2022, 1, 2, 0, 0)
        d_display = '02.01.2022'
        assert_equals(d_display, self.validator(d))
