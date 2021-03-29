from ckan.plugins.toolkit import missing, _
import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as tk
from ckanext.fluent.helpers import fluent_form_languages
from ckanext.scheming.helpers import scheming_field_choices
from ckanext.scheming.validation import scheming_validator
from ckanext.switzerland.helpers.localize_utils import parse_json
from ckanext.switzerland.helpers.dataset_form_helpers import (
    get_publishers_from_form,
    get_relations_from_form,
    get_see_alsos_from_form,
    get_temporals_from_form,
    get_contact_points_from_form)
from ckan.logic import NotFound, get_action
import json
import re
import datetime
import logging
log = logging.getLogger(__name__)

HARVEST_JUNK = ('__junk',)
FORM_EXTRAS = ('__extras',)
HARVEST_USER = 'harvest'

OneOf = tk.get_validator('OneOf')


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


def date_string_to_timestamp(value):
    """"
    Convert a date string (DD.MM.YYYY) into a POSIX timestamp to be stored.
    Necessary as the date form submits dates in this format.
    """
    try:
        date_format = tk.config.get(
            'ckanext.switzerland.date_picker_format', '%d.%m.%Y')
        d = datetime.datetime.strptime(str(value), date_format)
        epoch = datetime.datetime(1970, 1, 1)

        return int((d - epoch).total_seconds())
    except ValueError:
        return value


def timestamp_to_date_string(value):
    """
    Return a date string formatted for the datepicker (DD.MM.YYYY) for a given
    POSIX timestamp (1234567890).
    """
    try:
        dt = datetime.datetime.fromtimestamp(int(value))
    except ValueError:
        # The value is probably already formatted, so just return it.
        return value

    date_format = tk.config.get(
        'ckanext.switzerland.date_picker_format', '%d.%m.%Y')
    try:
        return dt.strftime(date_format)
    except ValueError:
        # The date is before 1900 so we have to format it ourselves.
        # See the docs for the Python 2 time library:
        # https://docs.python.org/2.7/library/time.html
        return date_format.replace('%d', str(dt.day).zfill(2))\
            .replace('%m', str(dt.month).zfill(2))\
            .replace('%Y', str(dt.year))


def temporals_to_datetime_output(value):
    """
    Converts a temporal with start and end date
    as timestamps to temporal as datetimes
    """
    value = parse_json(value)

    for temporal in value:
        for key in temporal:
            if temporal[key]:
                temporal[key] = timestamp_to_date_string(temporal[key])
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
        dataset_id = data.get(key[:-1] + ('id',))
        dataset_owner_org = data.get(key[:-1] + ('owner_org',))
        if not identifier:
            raise df.Invalid(
                _('Identifier of the dataset is missing.')
            )
        identifier_parts = identifier.split('@')
        if len(identifier_parts) == 1:
            raise df.Invalid(
                _('Identifier must be of the form <id>@<slug> where slug is the url of the organization.')  # noqa
            )
        identifier_org_slug = identifier_parts[1]
        try:
            dataset_organization = get_action('organization_show')(
                {},
                {'id': dataset_owner_org}
            )
            if dataset_organization['name'] != identifier_org_slug:
                raise df.Invalid(
                    _(
                        'The identifier "{}" does not end with the organisation slug "{}" of the organization it belongs to.'  # noqa
                        .format(identifier, dataset_organization['name']))  # noqa
                )
        except NotFound:
            raise df.Invalid(
                _('The selected organization was not found.')  # noqa
            )

        try:
            dataset_for_identifier = get_action('ogdch_dataset_by_identifier')(
                {},
                {'identifier': identifier}
            )
            if dataset_id != dataset_for_identifier['id']:
                raise df.Invalid(
                    _('Identifier is already in use, it must be unique.')
                )
        except NotFound:
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
            if publishers:
                output = [{'label': publisher} for publisher in publishers]
                data[key] = json.dumps(output)
            elif not _jsondata_for_key_is_set(data, key):
                data[key] = '{}'

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
            if contact_points:
                output = contact_points
                data[key] = json.dumps(output)
            elif not _jsondata_for_key_is_set(data, key):
                data[key] = '{}'

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
            elif not _jsondata_for_key_is_set(data, key):
                data[key] = '{}'

    return validator


@scheming_validator
def ogdch_validate_formfield_see_alsos(field, schema):
    """This validator is only used for form validation
    The data is extracted from the publisher form fields and transformed
    into a form that is expected for database storage:
    "see_alsos":
    [{"dataset_identifier": "443@statistisches-amt-kanton-zuerich"},
    {"dataset_identifier": "444@statistisches-amt-kanton-zuerich"},
    {"dataset_identifier": "10001@statistisches-amt-kanton-zuerich"}],
    """
    def validator(key, data, errors, context):
        extras = data.get(FORM_EXTRAS)
        see_alsos_validated = []
        if extras:
            see_alsos_from_form = get_see_alsos_from_form(extras)
            if see_alsos_from_form:
                context = {}
                for package_name in see_alsos_from_form:
                    try:
                        package = get_action('package_show')(context, {'id': package_name})  # noqa
                        if not package.get('type') == 'dataset':
                            raise df.Invalid(
                                _('{} can not be chosen since it is a {}.'
                                  .format(package_name, package.get('type')))
                            )
                        see_alsos_validated.append(
                            {'dataset_identifier': package.get('identifier')}
                        )
                    except NotFound:
                        raise df.Invalid(
                            _('Dataset {} could not be found .'
                              .format(package_name))
                        )
        if see_alsos_validated:
            data[key] = json.dumps(see_alsos_validated)
        elif not _jsondata_for_key_is_set(data, key):
            data[key] = '{}'

    return validator


@scheming_validator
def ogdch_validate_formfield_temporals(field, schema):
    """
    This validator is only used for form validation.
    The data is extracted form the temporals form fields and transformed
    into a form that is expected for database storage:
    "temporals": [{"start_date": 0123456789, "end_date": 0123456789}]
    """
    def validator(key, data, errors, context):
        extras = data.get(FORM_EXTRAS)
        temporals = []
        if extras:
            temporals = get_temporals_from_form(extras)
            for temporal in temporals:
                if not temporal['start_date'] and temporal['end_date']:
                    raise df.Invalid(
                        _('A valid temporal must have both start and end date')  # noqa
                    )
                temporal['start_date'] = date_string_to_timestamp(temporal['start_date'])  # noqa
                temporal['end_date'] = date_string_to_timestamp(temporal['end_date'])  # noqa
        if temporals:
            data[key] = json.dumps(temporals)
        elif not _jsondata_for_key_is_set(data, key):
            data[key] = '{}'

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
    """
    def validator(key, data, errors, context):
        if errors[key]:
            return

        value = json.loads(data[key])
        for lang in schema['form_languages']:
            if lang not in value.keys():
                value[lang] = []

        data[key] = json.dumps(value)

    return validator


@scheming_validator
def ogdch_temp_scheming_choices(field, schema):
    """
    Version of scheming_choices validator that allows inputs not included in
    the provided selection. Only used temporarily, while we transition to the
    new ogdch version and want to import existing datasets that have invalid
    data.
    """
    if 'choices' in field:
        return OneOf([c['value'] for c in field['choices']])

    def validator(value):
        if value is missing or not value:
            return value
        choices = scheming_field_choices(field)
        for c in choices:
            if value == c['value']:
                return value
        log.info(_('unexpected choice "%s"') % value)
        return value

    return validator


def _jsondata_for_key_is_set(data, key):
    """checks whether a key has already been set in the data: in that case the
    validator function has been replaced by a json string"""
    if key in data:
        return isinstance(data[key], basestring)
    else:
        return False
