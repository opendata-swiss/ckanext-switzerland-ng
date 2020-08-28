from ckan.plugins.toolkit import missing, _
import ckan.lib.navl.dictization_functions as df
from ckanext.fluent.helpers import fluent_form_languages
from ckanext.scheming.validation import scheming_validator
from ckanext.switzerland.helpers.localize_utils import parse_json
from ckanext.switzerland.helpers.dataset_form_helpers import (
    get_publishers_from_form,
    get_relations_from_form,
    get_contact_points_from_form,)
from ckan.logic import NotFound, get_action
import json
import re
import datetime
import logging
log = logging.getLogger(__name__)

HARVEST_JUNK = ('__junk',)
FORM_EXTRAS = ('__extras',)
HARVEST_USER = 'harvest'


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
            if isinstance(value, basestring):
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
    """
    Return stored json representation as a multilingual dict, if
    value is already a dict just pass it through.
    """
    if isinstance(value, dict):
        return value
    return parse_json(value)


def timestamp_to_datetime(value):
    """
    Returns a datetime for a given timestamp
    """
    try:
        return datetime.datetime.fromtimestamp(int(value)).isoformat()
    except ValueError:
        return False


def temporals_to_datetime_output(value):
    """
    Converts a temporal with start and end date
    as timestamps to temporal as datetimes
    """
    value = parse_json(value)

    for temporal in value:
        for key in temporal:
            if temporal[key]:
                temporal[key] = timestamp_to_datetime(temporal[key])
            else:
                temporal[key] = None
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
                if isinstance(value, basestring):
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
            pass

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
    choice_values = set(c['value'] for c in field['choices'])

    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        value = data[key]
        if value is not missing and value is not None:
            if isinstance(value, basestring):
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
            if (element in choice_values) or (re.match("^[a-z]{2}$", element)):
                selected.add(element)
                continue
            errors[key].append(_('invalid language "%s"') % element)

        if not errors[key]:
            data[key] = json.dumps([
                c['value'] for c in field['choices'] if c['value'] in selected
            ])

    return validator


@scheming_validator
def ogdch_unique_identifier(field, schema):
    def validator(key, data, errors, context):
        identifier = data.get(key[:-1] + ('identifier',))
        id = data.get(key[:-1] + ('id',))
        owner_org = data.get(key[:-1] + ('owner_org',))
        if not identifier:
            raise df.Invalid(
                _('Identifier of the dataset is missing.')
            )
        identifier_parts = identifier.split('@')
        if len(identifier_parts) == 1:
            raise df.Invalid(
                _('Identifier must be of the form <id>@<slug> where slug is the url of the organization.')  # noqa
            )
        owner_slug = identifier_parts[1]
        try:
            result = get_action('organization_show')(
                {},
                {'id': owner_slug}
            )
            if result['name'] != owner_org:
                raise df.Invalid(
                    _(
                        'Organisation slug of the identifier "{}" does not match the organisation of the dataset "{}".'  # noqa
                        .format(owner_slug, result['name']))  # noqa
                )
        except NotFound:
            raise df.Invalid(
                _('No organizations was found with the slug "{}".'.format(owner_slug))  # noqa
            )

        try:
            result = get_action('ogdch_dataset_by_identifier')(
                {},
                {'identifier': identifier}
            )
            if id != result['id']:
                raise df.Invalid(
                    _('Identifier is already in use, it must be unique.')
                )
        except NotFound:
            pass

    return validator


@scheming_validator
def ogdch_required_in_one_language(field, schema):
    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        output = {}
        prefix = key[-1] + '-'
        extras = data.get(key[:-1] + ('__extras',), {})
        languages = fluent_form_languages(field, schema=schema)

        for lang in languages:
            text = extras.get(prefix + lang)
            if text:
                output[lang] = text.strip()
                del extras[prefix + lang]
            elif data.get(key) and data.get(key).get(lang):
                output[lang] = data.get(key).get(lang)
            else:
                output[lang] = ''

        if not [lang for lang in languages if output[lang] != '']:
            for lang in languages:
                errors[key[:-1] + (key[-1] + '-' + lang,)] = \
                    [_('A value is required in at least one language')]
            return

        data[key] = json.dumps(output)

    return validator


@scheming_validator
def ogdch_validate_formfield_publishers(field, schema):
    """This validator is only used for form validation
    The data is extracted form the publisher form fields and transformed
    into a form that is expected for database storage:
    '[{'label': 'Publisher1'}, {'label': 'Publisher 2}]
    """
    def validator(key, data, errors, context):

        extras = data.get(FORM_EXTRAS)
        if extras:
            publishers = get_publishers_from_form(extras)

            if not publishers:
                raise df.Invalid(
                    _('At least one publisher must be provided.')  # noqa
                )
            output = [{'label': publisher} for publisher in publishers]
            data[key] = json.dumps(output)

    return validator


@scheming_validator
def ogdch_validate_formfield_contact_points(field, schema):
    """This validator is only used for form validation
    The data is extracted form the publisher form fields and transformed
    into a form that is expected for database storage:
    u'contact_points': [{u'email': u'tischhauser@ak-strategy.ch',
    u'name': u'tischhauser@ak-strategy.ch'}]
    """
    def validator(key, data, errors, context):

        extras = data.get(FORM_EXTRAS)
        if extras:
            contact_points = get_contact_points_from_form(extras)

            if not contact_points:
                raise df.Invalid(
                    _('At least one contact must be provided.')  # noqa
                )
            output = contact_points
            data[key] = json.dumps(output)

    return validator


@scheming_validator
def ogdch_validate_formfield_relations(field, schema):
    """This validator is only used for form validation
    The data is extracted form the publisher form fields and transformed
    into a form that is expected for database storage:
    "relations": [
    {"label": "legal_basis", "url": "https://www.admin.ch/#a20"},
    {"label": "legal_basis", "url": "https://www.admin.ch/#a21"}]
    """
    def validator(key, data, errors, context):

        extras = data.get(FORM_EXTRAS)
        if extras:
            relations = get_relations_from_form(extras)

            if relations:
                output = [{'label': relation['title'], 'url': relation['url']}
                          for relation in relations]
                data[key] = json.dumps(output)
            else:
                data[key] = '{}'

    return validator
