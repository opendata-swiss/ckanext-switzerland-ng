# encoding: utf-8

from nose.tools import assert_equals, assert_raises
from dateutil.parser import parse

from ckan.plugins.toolkit import get_validator, Invalid


class TestIValidators(object):

    def test_ogdch_date_validator_timestamp_to_isodate(self):
        d = parse('2022-01-02')
        v = get_validator('ogdch_date_validator')
        assert_equals(d.isoformat(), v(d))
