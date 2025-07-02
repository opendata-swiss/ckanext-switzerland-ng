import json
import logging
import re
from urllib.parse import urlparse

import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as tk
from ckan.lib.munge import munge_tag
from ckan.plugins.toolkit import _, missing

import ckanext.switzerland.helpers.date_helpers as ogdch_date_helpers
from ckanext.fluent.helpers import fluent_form_languages
from ckanext.scheming.helpers import scheming_field_choices
from ckanext.scheming.validation import register_validator, scheming_validator
from ckanext.switzerland.helpers.dataset_form_helpers import (
    get_contact_points_from_form,
    get_qualified_relations_from_form,
    get_relations_from_form,
    get_temporals_from_form,
)
from ckanext.switzerland.helpers.frontend_helpers import get_permalink
from ckanext.switzerland.helpers.localize_utils import LANGUAGES, parse_json

log = logging.getLogger(__name__)

HARVEST_JUNK = ("__junk",)
FORM_EXTRAS = ("__extras",)

OneOf = tk.get_validator("OneOf")


@scheming_validator
def multiple_text(field, schema):
    """
    Accept zero or more values as a list and convert
    to a json list for storage:
    1. a list of strings, eg.:
       ["somevalue a", "somevalue -b"]
    2. a single string for single item selection in form submissions:
       "somevalue-a"
    """

    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        # if errors[key]:
        #     return

        value = data[key]
        if value is not missing:
            if isinstance(value, str):
                value = [value]
            elif not isinstance(value, list):
                errors[key].append(
                    _('Expecting list of strings, got "%s"') % str(value)
                )
                return
        else:
            value = []

        if not errors[key]:
            data[key] = json.dumps(value)

    return validator


def multilingual_text_output(value):
    """Return stored json representation as a multilingual dict. If
    value is already a dict just pass it through.
    """
    if isinstance(value, dict):
        return value
    return parse_json(value)


@register_validator
def ogdch_date_validator(value):
    if value == ogdch_date_helpers.VALID_EMPTY_DATE:
        return value
    if value == ogdch_date_helpers.INVALID_EMPTY_DATE:
        return ogdch_date_helpers.correct_invalid_empty_date(value)

    display_value = ogdch_date_helpers.transform_any_date_to_isodate(value)
    if display_value:
        return display_value

    raise ogdch_date_helpers.OGDCHDateValidationException(
        f"Unknown date format detected in ogdch_date_validator : '{value}'"
    )


@register_validator
def ogdch_date_output(value):
    if value in ogdch_date_helpers.ACCEPTED_EMPTY_DATE_VALUES:
        return ogdch_date_helpers.VALID_EMPTY_DATE

    display_value = ogdch_date_helpers.transform_any_date_to_isodate(value)
    if display_value:
        return display_value

    raise ogdch_date_helpers.OGDCHDateValidationException(
        f"Unknown date format detected in ogdch_date_output : '{value}'"
    )


@register_validator
def temporals_display(value):
    """
    Converts a temporal with start and end date
    as timestamps to temporal as datetimes
    """
    value = parse_json(value)
    if not isinstance(value, list):
        return ""
    for temporal in value:
        for key in temporal:
            if temporal[key] is not None:
                temporal[key] = ogdch_date_output(temporal[key])
    return value


@scheming_validator
def harvest_list_of_dicts(field, schema):
    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        try:
            data_dict = df.unflatten(data[HARVEST_JUNK])
            value = data_dict[key[0]]
            if value is not missing:
                if isinstance(value, str):
                    value = [value]
                elif not isinstance(value, list):
                    errors[key].append(
                        _('Expecting list of strings, got "%s"') % str(value)
                    )
                    return
            else:
                value = []

            if not errors[key]:
                data[key] = json.dumps(value)

            # remove from junk
            del data_dict[key[0]]
            data[HARVEST_JUNK] = df.flatten_dict(data_dict)
        except KeyError:
            data[key] = json.dumps([])

    return validator


def multiple_text_output(value):
    """
    Return stored json representation as a list
    """
    return parse_json(value, default_value=[value])


@scheming_validator
def ogdch_language(field, schema):
    """
    Accept zero or more values from a list of choices and convert
    to a json list for storage:
    1. a list of strings, eg.:
       ["choice-a", "choice-b"]
    2. a single string for single item selection in form submissions:
       "choice-a"
    3. An ISO 639-1 two-letter language code (like en, de)
    """
    choice_values = set(c["value"] for c in field["choices"])

    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        value = data[key]
        if value is not missing and value is not None:
            if isinstance(value, str):
                value = [value]
            elif not isinstance(value, list):
                errors[key].append(
                    _('Expecting list of strings, got "%s"') % str(value)
                )
                return
        else:
            value = []

        selected = set()
        for element in value:
            # they are either explicit in the choice list or
            # match the ISO 639-1 two-letter pattern
            if (
                (element in choice_values)
                or (re.match("^[a-z]{2}$", element))
                or (
                    element.startswith(
                        "http://publications.europa.eu/resource/authority/language/"
                    )
                )
            ):
                selected.add(element)
                continue
            errors[key].append(_('invalid language "%s"') % element)

        if not errors[key]:
            data[key] = json.dumps(
                [c["value"] for c in field["choices"] if c["value"] in selected]
            )

    return validator


@scheming_validator
def ogdch_license_required(field, schema):
    def validator(key, data, errors, context):
        resource_id = data.get(key[:-1] + ("id",))
        license = data[key]
        if license not in (missing, None):
            data[key] = license
            return

        rights = data.get(key[:-1] + ("rights",))
        if rights not in (missing, None):
            log.debug(f"No license for resource {resource_id}, using rights instead")
            data[key] = rights
            return

        log.debug("Resource % has neither license nor rights")
        errors[key].append("Distributions must have 'license' property")
        data[key] = ""

    return validator


@scheming_validator
def ogdch_unique_identifier(field, schema):
    def validator(key, data, errors, context):
        identifier = data.get(key[:-1] + ("identifier",))
        dataset_id = data.get(key[:-1] + ("id",))
        dataset_owner_org = data.get(key[:-1] + ("owner_org",))
        if not identifier:
            raise df.Invalid(_("Identifier of the dataset is missing."))
        identifier_parts = identifier.split("@")
        if len(identifier_parts) == 1:
            raise df.Invalid(
                _(
                    "Identifier must be of the form <id>@<slug> where slug is the url "
                    "of the organization."
                )
            )
        identifier_org_slug = identifier_parts[1]
        try:
            dataset_organization = tk.get_action("organization_show")(
                {}, {"id": dataset_owner_org}
            )
            if dataset_organization["name"] != identifier_org_slug:
                raise df.Invalid(
                    _(
                        f'The identifier "{identifier}" does not end with the '
                        f"organisation slug \"{dataset_organization['name']}\" of the "
                        f"organization it belongs to."
                    )
                )
        except tk.ObjectNotFound:
            raise df.Invalid(_("The selected organization was not found."))

        try:
            dataset_for_identifier = tk.get_action("ogdch_dataset_by_identifier")(
                {}, {"identifier": identifier}
            )
            if dataset_id != dataset_for_identifier["id"]:
                raise df.Invalid(_("Identifier is already in use, it must be unique."))
        except tk.ObjectNotFound:
            pass

        data[key] = identifier

    return validator


@scheming_validator
def ogdch_required_in_one_language(field, schema):
    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        output = {}
        prefix = f"{key[-1]}-"
        extras = data.get(key[:-1] + FORM_EXTRAS, {})
        languages = fluent_form_languages(field, schema=schema)

        for lang in languages:
            text = extras.get(prefix + lang)
            if text:
                output[lang] = text.strip()
                del extras[prefix + lang]
            elif data.get(key) and data.get(key).get(lang):
                output[lang] = data.get(key).get(lang)
            else:
                output[lang] = ""

        if not [lang for lang in languages if output[lang] != ""]:
            for lang in languages:
                errors[key[:-1] + (f"{key[-1]}-{lang}",)] = [
                    _("A value is required in at least one language")
                ]
            return

        data[key] = json.dumps(output)

    return validator


@scheming_validator
def ogdch_validate_formfield_publisher(field, schema):
    """This validator is only used for form validation
    The data is extracted from the publisher form fields and transformed
    into a form that is expected for database storage:
    '{"name": {"de": "German Name", "en": "English Name", "fr": "French Name",
    "it": "Italian Name"}, "url": "Publisher URL"}'
    """

    def validator(key, data, errors, context):
        # the value is already a dict
        if isinstance(data.get(key), dict):
            data[key] = json.dumps(data.get(key))
            return  # exit early since this case is handled
        # the key is missing
        if not data.get(key):
            extras = data.get(FORM_EXTRAS)
            output = {"url": "", "name": {"de": "", "en": "", "fr": "", "it": ""}}
            if extras:
                publisher = _get_publisher_from_form(extras)
                if publisher:
                    output = publisher
                    output["name"] = {
                        "de": extras.get("publisher-name-de", ""),
                        "en": extras.get("publisher-name-en", ""),
                        "fr": extras.get("publisher-name-fr", ""),
                        "it": extras.get("publisher-name-it", ""),
                    }
                    if "publisher-url" in extras:
                        del extras["publisher-url"]
                    if any(
                        key.startswith("publisher-name-") for key in list(extras.keys())
                    ):
                        for lang in LANGUAGES:
                            lang_key = f"publisher-name-{lang}"
                            if lang_key in extras:
                                del extras[lang_key]
            data[key] = json.dumps(output)

    return validator


def _get_publisher_from_form(extras):
    if isinstance(extras, dict):
        publisher_fields = [
            (key, value.strip())
            for key, value in list(extras.items())
            if key.startswith("publisher-")
            if value.strip() != ""
        ]
        if not publisher_fields:
            return None
        else:
            publisher = {"url": "", "name": ""}
            publisher_url = [
                field[1] for field in publisher_fields if field[0] == "publisher-url"
            ]
            if publisher_url:
                publisher["url"] = publisher_url[0]
            publisher_name = [
                field[1] for field in publisher_fields if field[0] == "publisher-name"
            ]
            if publisher_name:
                publisher["name"] = publisher_name[0]
            return publisher
    return None


@scheming_validator
def ogdch_validate_formfield_contact_points(field, schema):
    """This validator is only used for form validation
    The data is extracted from the publisher form fields and transformed
    into a form that is expected for database storage:
    u'contact_points': [{u'email': u'tischhauser@ak-strategy.ch',
    u'name': u'tischhauser@ak-strategy.ch'}]
    """

    def validator(key, data, errors, context):

        extras = data.get(FORM_EXTRAS)
        if extras:
            contact_points = get_contact_points_from_form(extras)
            if contact_points:
                output = contact_points
                data[key] = json.dumps(output)
            elif not _jsondata_for_key_is_set(data, key):
                data[key] = "{}"

    return validator


@scheming_validator
def ogdch_validate_formfield_relations(field, schema):
    """This validator is only used for form validation
    The data is extracted from the publisher form fields and transformed
    into a form that is expected for database storage:
    "relations": [
        {"label": {"de: "text", "fr": "text", "it": "text", "en": "text"},
         "url": "https://www.admin.ch/#a20"},
        ...
    ]
    """

    def validator(key, data, errors, context):

        extras = data.get(FORM_EXTRAS)
        if extras:
            relations = get_relations_from_form(extras)
            if relations:
                data[key] = json.dumps(relations)
            elif not _jsondata_for_key_is_set(data, key):
                data[key] = "{}"

    return validator


@scheming_validator
def ogdch_validate_formfield_qualified_relations(field, schema):
    """This validator is only used for form validation
    The data is extracted from the publisher form fields and transformed
    into a form that is expected for database storage:
    [{
        "relation": "https://opendata.swiss/perma/443@statistisches-amt-kanton-zuerich",
        "had_role": "http://www.iana.org/assignments/relation/related"
    }]

    This corresponds to the DCAT class dcat:Relationship, which has the
    properties dct:relation and dcat:hadRole.
    """

    def validator(key, data, errors, context):
        extras = data.get(FORM_EXTRAS)
        qualified_relations_validated = []
        if extras:
            qualified_relations_from_form = get_qualified_relations_from_form(extras)
            if qualified_relations_from_form:
                context = {}
                for package_name in qualified_relations_from_form:
                    try:
                        package = tk.get_action("package_show")(
                            context, {"id": package_name}
                        )
                    except tk.ObjectNotFound:
                        raise df.Invalid(
                            _(f"Dataset {package_name} could not be found .")
                        )
                    if not package.get("type") == "dataset":
                        raise df.Invalid(
                            _(
                                f"{package_name} can not be chosen since it is a "
                                f"{package.get('type')}."
                            )
                        )
                    permalink = get_permalink(package.get("identifier"))
                    qualified_relations_validated.append(
                        {
                            "relation": permalink,
                            "had_role": "http://www.iana.org/assignments/relation/related",
                        }
                    )
        if qualified_relations_validated:
            data[key] = json.dumps(qualified_relations_validated)
        elif not _jsondata_for_key_is_set(data, key):
            data[key] = "[]"

    return validator


@scheming_validator
def ogdch_validate_temporals(field, schema):
    """Transforms temporal dates into the form that is expected for
    database storage:
    "temporals": [{"start_date": <date as isodate>,
    "end_date": <date as isodate>}]
    """

    def validator(key, data, errors, context):
        if key not in data:
            data[key] = "[]"
        else:
            temporals = []
            if not parse_json(data.get(key)):
                extras = data.get(FORM_EXTRAS)
                if extras:
                    temporals = get_temporals_from_form(extras)
                    for temporal in temporals:
                        if not temporal["start_date"] and temporal["end_date"]:
                            raise df.Invalid(
                                _("A valid temporal must have both start and end date")
                            )
            else:
                temporals = data[key]

            if not isinstance(temporals, list):
                temporals = json.loads(temporals)

            cleaned_temporals = []
            for temporal in temporals:
                cleaned_temporal = {}
                for k, v in list(temporal.items()):
                    cleaned_temporal[k] = ogdch_date_validator(v)
                cleaned_temporals.append(cleaned_temporal)

            data[key] = json.dumps(cleaned_temporals)

    return validator


@scheming_validator
def ogdch_fluent_tags(field, schema):
    """
    To be called after ckanext-fluent fluent_tags() because of an error that
    does not save any tag data for a language that has no tags entered, e.g. it
    would save {"de": ["tag-de"]} if German were the only language with a tag
    entered in the form. Not saving tag data for all the languages causes the
    tags to later be interpreted as a string, so here the dataset would display
    the tag '{u"de": [u"tag-de"]}' in every language.

    What we need to do in this case is save the tag field thus:
    {"de": ["tag-de"], "fr": [], "en": [], "it": []}

    Tags are munged to contain only lowercase letters, numbers, and the
    characters `-_.`
    """

    def validator(key, data, errors, context):
        if errors[key]:
            return

        value = json.loads(data[key])
        new_value = {}
        for lang in schema["form_languages"]:
            new_value[lang] = []
            if lang not in list(value.keys()):
                continue
            for keyword in value[lang]:
                new_value[lang].append(munge_tag(keyword))

        data[key] = json.dumps(new_value)

    return validator


@scheming_validator
def ogdch_temp_scheming_choices(field, schema):
    """
    Version of scheming_choices validator that allows inputs not included in
    the provided selection. Only used temporarily, while we transition to the
    new ogdch version and want to import existing datasets that have invalid
    data.
    """
    if "choices" in field:
        return OneOf([c["value"] for c in field["choices"]])

    def validator(value):
        if value is missing or not value:
            return value
        choices = scheming_field_choices(field)
        for c in choices:
            if value == c["value"]:
                return value
        log.info(_('unexpected choice "%s"') % value)
        return value

    return validator


def _jsondata_for_key_is_set(data, key):
    """checks whether a key has already been set in the data: in that case the
    validator function has been replaced by a json string"""
    if key in data:
        return isinstance(data[key], str)
    else:
        return False


@scheming_validator
def ogdch_validate_list_of_urls(field, schema):
    """Validates each url in a list (stored as json)."""

    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        value = data[key]
        if value is missing or not value:
            return value

        try:
            urls = json.loads(value)
        except (TypeError, ValueError):
            errors[key].append(f"Error parsing string as JSON: '{value}'")
            return value

        # Get rid of empty strings
        urls = [url for url in urls if url]

        for url in urls:
            result = urlparse(url)
            invalid = (
                not result.scheme
                or result.scheme not in ["http", "https"]
                or not result.netloc
            )
            if invalid:
                errors[key].append(f"Provided URL '{url}' is not valid")

        data[key] = json.dumps(urls)

    return validator


@scheming_validator
def ogdch_validate_list_of_uris(field, schema):
    """Validates each URI in a list (stored as JSON)."""

    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        value = data[key]
        if value is missing or not value:
            return value

        try:
            uris = json.loads(value)
        except (TypeError, ValueError):
            errors[key].append(f"Error parsing string as JSON: '{value}'")
            return value

        # Get rid of empty strings
        uris = [uri for uri in uris if uri]

        for uri in uris:
            result = urlparse(uri)
            invalid = not result.scheme or not result.netloc
            if invalid:
                errors[key].append(f"Provided URI '{uri}' is not valid")

        data[key] = json.dumps(uris)

    return validator


@scheming_validator
def ogdch_validate_duration_type(field, schema):
    """Validates that value is of type XSD.duration."""

    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        value = data[key]

        if value is missing or not value:
            data[key] = ""
            return

        duration_pattern = re.compile(
            r"^P(\d+Y)?(\d+M)?(\d+D)?(T(\d+H)?(\d+M)?(\d+(\.\d+)?S)?)?$"
        )
        if duration_pattern.match(value):
            data[key] = value
            return
        else:
            log.debug(f"Invalid value for XSD.duration: '{value}'")
            data[key] = ""
            return

    return validator
