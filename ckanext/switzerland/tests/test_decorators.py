# encoding: utf-8

from nose.tools import assert_equals, assert_raises
from unittest import TestCase
from datetime import datetime, timedelta
from ckanext.switzerland.helpers.decorators import ratelimit, _get_limits_from_config
from ckan.logic import ValidationError


class TestApiLimit(TestCase):
    def test_api_limit(self):
        """test that the api limit prevents successive calling with the same email"""
        @ratelimit
        def api_call(context, data_dict):
            if context.get('ratelimit_exceeded'):
                raise ValidationError("ratelimit exceeded")
            return True

        _, limit_call_count = _get_limits_from_config()
        context = {}
        data_dict = {'author_email': 'test@mail.com'}

        for i in range(limit_call_count):
            assert_equals(api_call(context=context, data_dict=data_dict), True)
        with self.assertRaises(ValidationError):
            api_call(context=context, data_dict=data_dict)