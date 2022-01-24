# encoding: utf-8
import datetime

from nose.tools import assert_equals, assert_raises
from dateutil.parser import parse, ParserError

from ckan.plugins.toolkit import get_validator, Invalid
from ckan import plugins


class TestIValidators(object):
    @classmethod
    def setup_class(cls):
        plugins.load('ogdch')

    @classmethod
    def teardown_class(cls):
        plugins.unload('ogdch')

    def test_ogdch_date_validator_timestamp_to_isodate(self):
        d = parse('2022-01-02')
        v = get_validator('ogdch_date_validator')
        assert_equals(d.isoformat(), v(d))
