# encoding: utf-8

from nose.tools import assert_equals

from ckanext.switzerland.helpers.date_helpers import transform_date_for_solr


class TestOgdchDateTransformationForSolr(object):
    def test_transform_of_isodate_without_tz(self):
        input = "2020-11-05T00:00:00"
        expected = "2020-11-05T00:00:00Z"
        output = transform_date_for_solr(input)
        assert_equals(output, expected)

    def test_transform_of_isodatetime_without_tz(self):
        input = "2020-11-05T15:30:04"
        expected = "2020-11-05T15:30:04Z"
        output = transform_date_for_solr(input)
        assert_equals(output, expected)

    def test_transform_of_isodatetime_with_tz(self):
        input = "2022-10-11T15:30:04.359000+02:00"
        expected = "2022-10-11T15:30:04Z"
        output = transform_date_for_solr(input)
        assert_equals(output, expected)
