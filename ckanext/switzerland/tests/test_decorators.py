from unittest import TestCase

from ckan.logic import ValidationError

from ckanext.switzerland.helpers.decorators import _get_limits_from_config, ratelimit


class TestApiLimit(TestCase):
    def test_api_limit(self):
        """Test that the api limit prevents successive calling with the same email"""

        @ratelimit
        def api_call(context, data_dict):
            if context.get("ratelimit_exceeded"):
                raise ValidationError("Rate limit exceeded")
            return True

        _, limit_call_count = _get_limits_from_config()
        context = {}
        data_dict = {"author_email": "test@mail.com"}

        for i in range(limit_call_count):
            assert api_call(context=context, data_dict=data_dict) is True
        with self.assertRaises(ValidationError):
            api_call(context=context, data_dict=data_dict)
