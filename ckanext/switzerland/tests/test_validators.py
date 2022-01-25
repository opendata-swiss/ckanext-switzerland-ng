# encoding: utf-8

from nose.tools import assert_equals, assert_raises
from dateutil.parser import parse
from datetime import datetime

from ckan.plugins.toolkit import get_validator, Invalid


class TestOgdchDateValidators(object):
    def setup(self):
        self.validator = get_validator('ogdch_date_validator')

    def test_ogdch_date_validator_parseeable_date_to_isodate(self):
        d = parse('2022-01-02').isoformat()
        d_isodate = d.isoformat()
        assert_equals(d_isodate, self.validator(d))

    def test_ogdch_date_validator_isodate_to_isodate(self):
        d = parse('2022-01-02').isoformat()
        assert_equals(d, self.validator(d))

    def test_ogdch_german_date_to_isodate(self):
        d = '02.04.2020'
        d_isodate = parse(d, dayfirst=True).isoformat()
        assert_equals(d_isodate, self.validator(d))

    def test_timestamp_to_isodate(self):
        date_value = parse(str('04.05.2000'), dayfirst=True)
        epoch = datetime(1970, 1, 1)
        d = int((date_value - epoch).total_seconds())
        d_isodate = date_value.isoformat()
        assert_equals(d_isodate, self.validator(d))

    def test_ogdch_date_validator_isodate_before_1870_to_isodate(self):
        d = parse('1655-01-02').isoformat()
        assert_equals(d, self.validator(d))
