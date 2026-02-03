import pytest
from ckan.lib.navl.dictization_functions import Invalid
from ckan.logic.validators import missing
from ckan.plugins.toolkit import get_validator


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch",
)
@pytest.mark.usefixtures("with_plugins")
class TestOgdchUrlListValidator(object):
    def test_validate_url_list_string(self):
        value = '["https://example.com/1", "http://example.com/2"]'
        key = "documentation"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        # We pass in dummy values for field and schema here, because we just
        # want to get the inner validation function, and that does not use
        # either of these parameters.
        validator = get_validator("ogdch_validate_list_of_urls")("field", {})
        validator(key, data, errors, {})

        assert value == data[key]
        assert [] == errors[key]

    def test_validate_url_list_string_with_invalid_url(self):
        value = '["http://example.com/foo", "foobar"]'
        key = "documentation"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_validate_list_of_urls")("field", {})
        validator(key, data, errors, {})

        assert value == data[key]
        assert ["Provided URL 'foobar' is not valid"] == errors[key]


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch",
)
@pytest.mark.usefixtures("with_plugins")
class TestOgdchUriListValidator(object):
    # positive tests
    def test_validate_uri_list_string(self):
        value = '["http://example.com/1", "https://example.com/2", "ftp://example.com"]'
        key = "conforms_to"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_validate_list_of_uris")("field", {})
        validator(key, data, errors, {})

        assert value == data[key]
        assert [] == errors[key]

    # negative tests
    def test_invalid_uri_list_string(self):
        value = '["invaliduri", "ftp://example.com"]'
        key = "conforms_to"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_validate_list_of_uris")("field", {})
        validator(key, data, errors, {})

        assert value == data[key]
        assert ["Provided URI 'invaliduri' is not valid"] == errors[key]

    def test_empty_uri_list_string(self):
        value = '["", ""]'
        key = "conforms_to"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_validate_list_of_uris")("field", {})
        validator(key, data, errors, {})

        assert "[]" == data[key]
        assert [] == errors[key]


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch",
)
@pytest.mark.usefixtures("with_plugins")
class TestOgdchLicenseRequiredValidator(object):
    def setup(self):
        self.validator = get_validator("ogdch_license_required")("field", {})

    def test_validate_license(self):
        value = "Creative Commons CC Zero License (cc-zero)"
        key = ("resources", 0, "license")
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_license_required")("field", {})
        validator(key, data, errors, {})

        assert value == data[key]
        assert [] == errors[key]

    def test_validate_rights(self):
        value = missing
        key = ("resources", 0, "license")
        rights_value = "NonCommercialAllowed-CommercialAllowed-ReferenceRequired"
        rights_key = ("resources", 0, "rights")

        data = {
            key: value,
            rights_key: rights_value,
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_license_required")("field", {})
        validator(key, data, errors, {})

        assert "NonCommercialAllowed-CommercialAllowed-ReferenceRequired" == data[key]
        assert [] == errors[key]

    def test_validate_both_license_and_rights(self):
        value = "Creative Commons CC Zero License (cc-zero)"
        key = ("resources", 0, "license")
        rights_value = "NonCommercialAllowed-CommercialAllowed-ReferenceRequired"
        rights_key = ("resources", 0, "rights")

        data = {
            key: value,
            rights_key: rights_value,
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_license_required")("field", {})
        validator(key, data, errors, {})

        assert value == data[key]
        assert [] == errors[key]

    def test_validate_neither_licence_nor_rights(self):
        value = missing
        key = ("resources", 0, "license")
        rights_value = missing
        rights_key = ("resources", 0, "rights")
        data = {
            key: value,
            rights_key: rights_value,
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_license_required")("field", {})
        validator(key, data, errors, {})

        assert "" == data[key]
        assert ["Distributions must have 'license' property"] == errors[key]


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch",
)
@pytest.mark.usefixtures("with_plugins")
class TestOgdchDurationType(object):
    # positive tests
    def test_valid_duration(self):
        value = "P1Y2M3DT4H5M6S"
        key = "temporal_resolution"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_validate_duration_type")("field", {})
        validator(key, data, errors, {})

        assert value == data[key]
        assert [] == errors[key]

    # negative tests
    def test_empty_value(self):
        key = "temporal_resolution"
        data = {
            key: "",
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_validate_duration_type")("field", {})
        validator(key, data, errors, {})

        assert "" == data[key]
        assert [] == errors[key]

    def test_missing_value(self):
        key = "temporal_resolution"
        data = {}
        errors = {
            key: [],
        }
        data[key] = {}

        validator = get_validator("ogdch_validate_duration_type")("field", {})
        validator(key, data, errors, {})

        assert "" == data[key]
        assert [] == errors[key]

    def test_invalid_duration(self):
        value = "InvalidDuration"
        key = "temporal_resolution"
        data = {
            key: value,
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_validate_duration_type")("field", {})
        validator(key, data, errors, {})

        assert "" == data[key]
        assert [] == errors[key]


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch ogdch_pkg scheming_datasets fluent",
)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestOgdchUniqueIdentifierValidator(object):
    def test_unique_identifier(self, org, dataset):
        value = "really_unique_identifier@test-org"
        key = ("identifier",)
        data = {
            key: value,
            ("owner_org",): "test-org",
        }
        errors = {
            key: [],
        }
        validator = get_validator("ogdch_unique_identifier")("field", {})
        validator(key, data, errors, {})

    def test_non_unique_identifier(self, org, dataset):
        value = "test@test-org"
        key = ("identifier",)
        data = {
            key: value,
            ("owner_org",): "test-org",
        }
        errors = {
            key: [],
        }
        with pytest.raises(
            Invalid, match="Identifier is already in use, it must be unique."
        ):
            validator = get_validator("ogdch_unique_identifier")("field", {})
            validator(key, data, errors, {})

    def test_missing_identifier(self, org, dataset):
        key = ("identifier",)
        data = {
            ("owner_org",): "test-org",
        }
        errors = {
            key: [],
        }
        with pytest.raises(Invalid, match="Identifier of the dataset is missing."):
            validator = get_validator("ogdch_unique_identifier")("field", {})
            validator(key, data, errors, {})

    def test_malformed_identifier(self, org, dataset):
        value = "identifier at test-org"
        key = ("identifier",)
        data = {
            key: value,
            ("owner_org",): "test-org",
        }
        errors = {
            key: [],
        }
        with pytest.raises(Invalid, match="Identifier must be of the form <id>@<slug>"):
            validator = get_validator("ogdch_unique_identifier")("field", {})
            validator(key, data, errors, {})

    def test_mismatched_org(self, org, dataset):
        value = "identifier@my-org"
        key = ("identifier",)
        data = {
            key: value,
            ("owner_org",): "test-org",
        }
        errors = {
            key: [],
        }
        with pytest.raises(
            Invalid,
            match='The identifier "identifier@my-org" does not end with the '
            'organisation slug "test-org"',
        ):
            validator = get_validator("ogdch_unique_identifier")("field", {})
            validator(key, data, errors, {})

    def test_nonexistent_org(self, org, dataset):
        value = "identifier@my-org"
        key = ("identifier",)
        data = {
            key: value,
            ("owner_org",): "my-org",
        }
        errors = {
            key: [],
        }
        with pytest.raises(Invalid, match="The selected organization was not found."):
            validator = get_validator("ogdch_unique_identifier")("field", {})
            validator(key, data, errors, {})
