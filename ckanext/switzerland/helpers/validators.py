from ckan.plugins.toolkit import missing, _, get_validator
import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as tk
from ckanext.fluent.helpers import (
    fluent_form_languages, fluent_alternate_languages)
from ckanext.fluent.validators import BCP_47_LANGUAGE, _validate_single_tag
from ckanext.scheming.validation import (
    scheming_validator, validators_from_string)
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

tag_length_validator = get_validator('tag_length_validator')
tag_name_validator = get_validator('tag_name_validator')


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
        date_format = tk.config.get('ckanext.switzerland.date_picker_format')
        d = datetime.datetime.strptime(str(value), date_format)
        epoch = datetime.datetime(1970, 1, 1)

        return int((d - epoch).total_seconds())
    except ValueError:
        return value


def timestamp_to_date_string(value):
    """
    Return a date string formatted for the datepicker (DD.MM.YYYY) for a given
    POSIX timestamp (1234567890).
    If we get a ValueError, the value is probably already formatted, so just
    return it.
    """
    try:
        dt = datetime.datetime.fromtimestamp(int(value))
        date_format = tk.config.get('ckanext.switzerland.date_picker_format')
        return dt.strftime(date_format)
    except ValueError:
        return value


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

#            if not publishers:
#                raise df.Invalid(
#                    _('At least one publisher must be provided.')  # noqa
#                )
            if publishers:
                output = [{'label': publisher} for publisher in publishers]
                data[key] = json.dumps(output)
            else:
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

#            if not contact_points:
#                raise df.Invalid(
#                    _('At least one contact must be provided.')  # noqa
#                )
            if contact_points:
                output = contact_points
                data[key] = json.dumps(output)
            else:
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
            else:
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
        else:
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
        else:
            data[key] = '{}'

    return validator


@scheming_validator
def ogdch_fluent_tags(field, schema):
    """
    Overridden from ckanext-fluent fluent_tags() because of an error that does
    not save any tag data for a language that has no tags entered, e.g. it
    would save {"de": ["tag-de"]} if German were the only language with a tag
    entered in the form. Not saving tag data for all the languages causes the
    tags to later be interpreted as a string, so here the dataset would display
    the tag '{u"de": [u"tag-de"]}' in every language.

    What we need to do in this case is save the tag field thus:
    {"de": ["tag-de"], "fr": [], "en": [], "it": []}
    """

    required_langs = []
    alternate_langs = {}
    if field and field.get('required'):
        required_langs = fluent_form_languages(field, schema=schema)
        alternate_langs = fluent_alternate_languages(field, schema=schema)

    tag_validators = [tag_length_validator, tag_name_validator]
    if field and 'tag_validators' in field:
        tag_validators = validators_from_string(
            field['tag_validators'], field, schema)

    def validator(key, data, errors, context):
        if errors[key]:
            return

        value = data[key]
        # 1. dict of lists of tag strings
        if value is not missing:
            if not isinstance(value, dict):
                errors[key].append(_('expecting JSON object'))
                return

            for lang, keys in value.items():
                try:
                    m = re.match(BCP_47_LANGUAGE, lang)
                except TypeError:
                    errors[key].append(_('invalid type for language code: %r')
                                       % lang)
                    continue
                if not m:
                    errors[key].append(_('invalid language code: "%s"') % lang)
                    continue
                if not isinstance(keys, list):
                    errors[key].append(_('invalid type for "%s" value') % lang)
                    continue
                out = []
                for i, v in enumerate(keys):
                    if not isinstance(v, basestring):
                        errors[key].append(
                            _('invalid type for "{lang}" value item {num}').format(
                                lang=lang, num=i))
                        continue

                    if isinstance(v, str):
                        try:
                            out.append(v.decode('utf-8'))
                        except UnicodeDecodeError:
                            errors[key]. append(_(
                                'expected UTF-8 encoding for '
                                '"{lang}" value item {num}').format(
                                lang=lang, num=i))
                    else:
                        out.append(v)

                tags = []
                errs = []
                for tag in out:
                    newtag, tagerrs = _validate_single_tag(tag, tag_validators)
                    errs.extend(tagerrs)
                    tags.append(newtag)
                if errs:
                    errors[key].extend(errs)
                value[lang] = tags

            for lang in required_langs:
                if value.get(lang) or any(
                        value.get(l) for l in alternate_langs.get(lang, [])):
                    continue
                errors[key].append(_('Required language "%s" missing') % lang)

            if not errors[key]:
                data[key] = json.dumps(value)
            return

        # 2. separate fields
        output = {}
        prefix = key[-1] + '-'
        extras = data.get(key[:-1] + ('__extras',), {})

        for name, text in extras.iteritems():
            if not name.startswith(prefix):
                continue
            lang = name.split('-', 1)[1]
            m = re.match(BCP_47_LANGUAGE, lang)
            if not m:
                errors[name] = [_('invalid language code: "%s"') % lang]
                output = None
                continue

            if not isinstance(text, basestring):
                errors[name].append(_('invalid type'))
                continue

            if isinstance(text, str):
                try:
                    text = text.decode('utf-8')
                except UnicodeDecodeError:
                    errors[name].append(_('expected UTF-8 encoding'))
                    continue

            if output is not None:
                if text:
                    tags = []
                    errs = []
                    for tag in text.split(','):
                        newtag, tagerrs = _validate_single_tag(tag, tag_validators)
                        errs.extend(tagerrs)
                        tags.append(newtag)
                    output[lang] = tags
                    if errs:
                        errors[key[:-1] + (name,)] = errs
                else:
                    output[lang] = []

        for lang in required_langs:
            if extras.get(prefix + lang) or any(
                    extras.get(prefix + l) for l in alternate_langs.get(lang, [])):
                continue
            errors[key[:-1] + (key[-1] + '-' + lang,)] = [_('Missing value')]
            output = None

        if output is None:
            return

        for lang in output:
            del extras[prefix + lang]
        data[key] = json.dumps(output)

    return validator
