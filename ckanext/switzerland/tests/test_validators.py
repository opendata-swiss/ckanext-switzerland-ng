# encoding: utf-8

from nose.tools import assert_equals, assert_raises
from dateutil.parser import parse
from datetime import datetime

from ckan.plugins.toolkit import get_validator, Invalid


class TestOgdchDateValidators(object):
    def setup(self):
        self.validator = get_validator('ogdch_date_validator')
    def test_ogdch_date_validator_parseeable_date_to_isodate(self):
        datetime_value = parse('2022-01-02')
        value_as_isodate = datetime_value.isoformat()
        assert_equals(value_as_isodate, self.validator(datetime_value))

    def test_ogdch_date_validator_isodate_to_isodate(self):
        isodate_value = parse('2022-01-02').isoformat()
        value_as_isodate = isodate_value
        assert_equals(isodate_value, self.validator(value_as_isodate))

    def test_ogdch_german_date_to_isodate(self):
        german_date_value = '02.04.2020'
        value_as_isodate = parse(german_date_value, dayfirst=True).isoformat()
        assert_equals(value_as_isodate, self.validator(german_date_value))

    def test_timestamp_to_isodate(self):
        date_value = parse(str('04.05.2000'), dayfirst=True)
        epoch = datetime(1970, 1, 1)
        timestamp_value = int((date_value - epoch).total_seconds())
        date_value_as_isodate = date_value.isoformat()
        assert_equals(date_value_as_isodate, self.validator(timestamp_value))

    def test_ogdch_date_validator_isodate_before_1870_to_isodate(self):
        isodate_value = parse('1655-01-02').isoformat()
        value_as_isodate = isodate_value
        assert_equals(isodate_value, self.validator(value_as_isodate))