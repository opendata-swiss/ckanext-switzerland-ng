from datetime import datetime

import pytest
from dateutil.parser import parse

from ckanext.switzerland.helpers.date_helpers import OGDCHDateValidationException
from ckanext.switzerland.helpers.validators import (
    ogdch_date_output,
    ogdch_date_validator,
)


class TestOgdchDateStorageValidator(object):
    def test_ogdch_date_validator_parseeable_date_to_isodate(self):
        d = parse("2022-01-02")
        d_storage = d.isoformat()
        assert d_storage == ogdch_date_validator(d)

    def test_ogdch_date_validator_isodate_to_isodate(self):
        d = parse("2022-01-02").isoformat()
        d_storage = d
        assert d_storage == ogdch_date_validator(d)

    def test_ogdch_german_date_to_isodate(self):
        d = "02.04.2020"
        d_storage = parse(d, dayfirst=True).isoformat()
        assert d_storage == ogdch_date_validator(d)

    def test_timestamp_to_isodate(self):
        date_value = parse(str("04.05.2000"), dayfirst=True)
        epoch = datetime(1970, 1, 1)
        d = int((date_value - epoch).total_seconds())
        d_storage = date_value.isoformat()
        assert d_storage == ogdch_date_validator(d)

    def test_ogdch_date_validator_isodate_before_1870_to_isodate(self):
        d = parse("1655-01-02").isoformat()
        d_storage = d
        assert d_storage == ogdch_date_validator(d)

    def test_ogdch_date_validator_datetime_to_isodate(self):
        d = datetime(2022, 1, 2, 0, 0)
        d_storage = d.isoformat()
        assert d_storage == ogdch_date_validator(d)

    def test_ogdch_date_validator_parseeable_with_timezone_to_isodate(self):
        d = "2008-09-03T20:56:35.450686Z"
        d_storage = d
        assert d_storage == ogdch_date_validator(d)

    def test_ogdch_date_validator_empty_date_value(self):
        d = ""
        d_storage = d
        assert d_storage == ogdch_date_validator(d)

    def test_ogdch_date_validator_null_date_value(self):
        d = "False"
        d_storage = ""
        assert d_storage == ogdch_date_validator(d)

    def test_ogdch_date_validator_unknown_date_value(self):
        d = "Hallo"
        with pytest.raises(OGDCHDateValidationException):
            ogdch_date_validator(d)


class TestOgdchDateDisplayValidator(object):
    def test_ogdch_date_validator_parsed_date(self):
        d = parse("2022-01-02")
        d_display = "2022-01-02T00:00:00"
        assert d_display == ogdch_date_output(d)

    def test_ogdch_date_validator_isodate(self):
        d = "2022-01-02T00:00:00"
        d_display = "2022-01-02T00:00:00"
        assert d_display == ogdch_date_output(d)

    def test_ogdch_date_validator_isodate_with_time_component(self):
        d = "2022-01-02T12:10:10"
        d_display = "2022-01-02T12:10:10"
        assert d_display == ogdch_date_output(d)

    def test_ogdch_date_validator_date_picker_date(self):
        d = "02.04.2020"
        d_display = "2020-04-02T00:00:00"
        assert d_display == ogdch_date_output(d)

    def test_ogdch_date_validator_timestamp(self):
        date_value = parse(str("04.05.2000"), dayfirst=True)
        epoch = datetime(1970, 1, 1)
        d = int((date_value - epoch).total_seconds())
        d_display = "2000-05-04T00:00:00"
        assert d_display == ogdch_date_output(d)

    def test_ogdch_date_validator_isodate_before_1870(self):
        d = parse("1655-01-02").isoformat()
        d_display = "1655-01-02T00:00:00"
        assert d_display == ogdch_date_output(d)

    def test_ogdch_date_validator_datetime(self):
        d = datetime(2022, 1, 2, 0, 0)
        d_display = "2022-01-02T00:00:00"
        assert d_display == ogdch_date_output(d)

    def test_display_empty_date_value(self):
        d = ""
        d_display = d
        assert d_display == ogdch_date_output(d)

    def test_display_false_date_value(self):
        d = "False"
        d_display = ""
        assert d_display == ogdch_date_output(d)

    def test_display_unknown_date_value(self):
        d = "Hallo"
        with pytest.raises(OGDCHDateValidationException):
            ogdch_date_output(d)
