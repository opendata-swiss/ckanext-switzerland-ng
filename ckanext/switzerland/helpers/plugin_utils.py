"""
helpers of the plugins.py
"""
import json
import re
from ckan import logic
import ckan.plugins.toolkit as toolkit
from ckan.lib.munge import munge_title_to_name
import ckanext.switzerland.helpers.localize_utils as ogdch_loc_utils
import ckanext.switzerland.helpers.terms_of_use_utils as ogdch_term_utils
import ckanext.switzerland.helpers.format_utils as ogdch_format_utils
import ckanext.switzerland.helpers.request_utils as ogdch_request_utils
from dateutil.parser import parse, ParserError


def _prepare_suggest_context(search_data, pkg_dict):
    def clean_suggestion(term):
        return term.replace('-', '')

    search_data['suggest_groups'] = [clean_suggestion(t['name']) for t in pkg_dict['groups']]  # noqa
    search_data['suggest_organization'] = clean_suggestion(pkg_dict['organization']['name'])  # noqa

    search_data['suggest_tags'] = []
    search_data['suggest_tags'].extend([clean_suggestion(t) for t in search_data.get('keywords_de', [])])  # noqa
    search_data['suggest_tags'].extend([clean_suggestion(t) for t in search_data.get('keywords_fr', [])])  # noqa
    search_data['suggest_tags'].extend([clean_suggestion(t) for t in search_data.get('keywords_it', [])])  # noqa
    search_data['suggest_tags'].extend([clean_suggestion(t) for t in search_data.get('keywords_en', [])])  # noqa

    search_data['suggest_res_rights'] = [clean_suggestion(t) for t in search_data['res_rights']]  # noqa
    search_data['suggest_res_format'] = [clean_suggestion(t) for t in search_data['res_format']]  # noqa

    return search_data


def map_ckan_default_fields(pkg_dict):  # noqa
    pkg_dict['display_name'] = pkg_dict['title']

    if pkg_dict.get('maintainer') is None:
        try:
            pkg_dict['maintainer'] = pkg_dict['contact_points'][0]['name']  # noqa
        except (KeyError, IndexError):
            pass

    if pkg_dict.get('maintainer_email') is None:
        try:
            pkg_dict['maintainer_email'] = pkg_dict['contact_points'][0]['email']  # noqa
        except (KeyError, IndexError):
            pass

    if pkg_dict.get('author') is None:
        try:
            pkg_dict['author'] = pkg_dict['publisher']['name']  # noqa
        except KeyError:
            pass

    if pkg_dict.get('resources') is not None:
        for resource in pkg_dict['resources']:
            resource['name'] = resource['title']

    return pkg_dict


def _is_dataset_package_type(pkg_dict):
    """determines whether a packages is a dataset"""
    try:
        return (pkg_dict['type'] == 'dataset')
    except KeyError:
        return False


def ogdch_prepare_search_data_for_index(search_data, format_mapping):  # noqa
    """prepares the data for indexing"""
    if not _is_dataset_package_type(search_data):
        return search_data

    validated_dict = json.loads(search_data['validated_data_dict'])

    search_data['res_name'] = [ogdch_loc_utils.lang_to_string(r, 'title') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_en'] = [ogdch_loc_utils.get_localized_value_from_dict(r['title'], 'en') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_de'] = [ogdch_loc_utils.get_localized_value_from_dict(r['title'], 'de') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_fr'] = [ogdch_loc_utils.get_localized_value_from_dict(r['title'], 'fr') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_it'] = [ogdch_loc_utils.get_localized_value_from_dict(r['title'], 'it') for r in validated_dict[u'resources']]  # noqa
    search_data['res_description_en'] = [ogdch_loc_utils.get_localized_value_from_dict(r['description'], 'en') for r in validated_dict[u'resources']]  # noqa
    search_data['res_description_de'] = [ogdch_loc_utils.get_localized_value_from_dict(r['description'], 'de') for r in validated_dict[u'resources']]  # noqa
    search_data['res_description_fr'] = [ogdch_loc_utils.get_localized_value_from_dict(r['description'], 'fr') for r in validated_dict[u'resources']]  # noqa
    search_data['res_description_it'] = [ogdch_loc_utils.get_localized_value_from_dict(r['description'], 'it') for r in validated_dict[u'resources']]  # noqa
    search_data['groups_en'] = [ogdch_loc_utils.get_localized_value_from_dict(g['display_name'], 'en') for g in validated_dict[u'groups']]  # noqa
    search_data['groups_de'] = [ogdch_loc_utils.get_localized_value_from_dict(g['display_name'], 'de') for g in validated_dict[u'groups']]  # noqa
    search_data['groups_fr'] = [ogdch_loc_utils.get_localized_value_from_dict(g['display_name'], 'fr') for g in validated_dict[u'groups']]  # noqa
    search_data['groups_it'] = [ogdch_loc_utils.get_localized_value_from_dict(g['display_name'], 'it') for g in validated_dict[u'groups']]  # noqa
    search_data['res_description'] = [ogdch_loc_utils.lang_to_string(r, 'description') for r in validated_dict[u'resources']]  # noqa
    search_data['res_format'] = ogdch_format_utils.prepare_formats_for_index(
        resources=validated_dict[u'resources'],
        format_mapping=format_mapping
    )  # noqa
    search_data['res_rights'] = [ogdch_term_utils.simplify_terms_of_use(r['rights']) for r in validated_dict[u'resources'] if 'rights' in r.keys()]  # noqa
    search_data['title_string'] = ogdch_loc_utils.lang_to_string(validated_dict, 'title') # noqa
    search_data['description'] = ogdch_loc_utils.lang_to_string(validated_dict, 'description')  # noqa
    if 'political_level' in validated_dict[u'organization']:
        search_data['political_level'] = validated_dict[u'organization'][u'political_level']  # noqa

    search_data['identifier'] = validated_dict.get('identifier')
    search_data['contact_points'] = [c['name'] for c in validated_dict.get('contact_points', [])]  # noqa
    if 'publisher' in validated_dict:
        publisher = json.loads(validated_dict['publisher'])
        search_data['publisher'] = publisher.get('name', '')  # noqa
        search_data['publisher_url'] =publisher.get('url', '')  # noqa

    # TODO: Remove the try-except-block.
    # This fixes the index while we have 'wrong' relations on
    # datasets harvested with an old version of ckanext-geocat
    try:
        search_data['see_alsos'] = [d['dataset_identifier'] for d in validated_dict.get('see_alsos', [])]  # noqa
    except TypeError:
        search_data['see_alsos'] = [d for d in
                                    validated_dict.get('see_alsos',
                                                       [])]  # noqa

    # make sure we're not dealing with NoneType
    if search_data['metadata_created'] is None:
        search_data['metadata_created'] = ''

    if search_data['metadata_modified'] is None:
        search_data['metadata_modified'] = ''

    try:
        # index language-specific values (or it's fallback)
        for lang_code in ogdch_loc_utils.get_language_priorities():
            search_data['title_' + lang_code] = \
                ogdch_loc_utils.get_localized_value_from_dict(
                    validated_dict['title'], lang_code)
            search_data['title_string_' + lang_code] = munge_title_to_name(
                ogdch_loc_utils.get_localized_value_from_dict(
                    validated_dict['title'], lang_code))
            search_data['description_' + lang_code] = \
                ogdch_loc_utils.get_localized_value_from_dict(
                    validated_dict['description'], lang_code)
            search_data['keywords_' + lang_code] = \
                ogdch_loc_utils.get_localized_value_from_dict(
                   validated_dict['keywords'], lang_code)
            search_data['organization_' + lang_code] = \
                ogdch_loc_utils.get_localized_value_from_dict(  # noqa
                    validated_dict['organization']['title'], lang_code)

    except KeyError:
        pass

    # clean terms for suggest context
    search_data = _prepare_suggest_context(
        search_data,
        validated_dict
    )

    return search_data


def package_map_ckan_default_fields(pkg_dict):  # noqa
    pkg_dict['display_name'] = pkg_dict['title']

    if pkg_dict.get('maintainer') is None:
        try:
            pkg_dict['maintainer'] = pkg_dict['contact_points'][0]['name']  # noqa
        except (KeyError, IndexError):
            pass

    if pkg_dict.get('maintainer_email') is None:
        try:
            pkg_dict['maintainer_email'] = pkg_dict['contact_points'][0]['email']  # noqa
        except (KeyError, IndexError):
            pass

    if pkg_dict.get('author') is None:
        try:
            pkg_dict['author'] = pkg_dict['publisher']['name']  # noqa
        except (KeyError, TypeError):
            pass

    if pkg_dict.get('resources') is not None:
        for resource in pkg_dict['resources']:
            resource['name'] = resource['title']

    return pkg_dict


def ogdch_prepare_pkg_dict_for_api(pkg_dict):
    if not _is_dataset_package_type(pkg_dict):
        return pkg_dict

    pkg_dict = package_map_ckan_default_fields(pkg_dict)

    # groups
    if pkg_dict['groups'] is not None:
        for group in pkg_dict['groups']:
            """
            TODO: somehow the title is messed up here,
            but the display_name is okay
            """
            group['title'] = group['display_name']
            for field in group:
                group[field] = ogdch_loc_utils.parse_json(group[field])

    # load organization from API to get all fields defined in schema
    # by default, CKAN loads organizations only from the database
    if pkg_dict['owner_org'] is not None:
        pkg_dict['organization'] = logic.get_action('organization_show')(
            {},
            {
                'id': pkg_dict['owner_org'],
                'include_users': False,
                'include_followers': False,
            }
        )

    if ogdch_request_utils.request_is_api_request():
        _transform_package_dates(pkg_dict)
        _transform_publisher(pkg_dict)
    return pkg_dict


def ogdch_adjust_search_params(search_params):
    """search in correct language-specific field and boost
    results in current language
    borrowed from ckanext-multilingual (core extension)"""
    lang_set = ogdch_loc_utils.get_language_priorities()
    try:
        current_lang = toolkit.request.environ['CKAN_LANG']
    except TypeError as err:
        if err.message == ('No object (name: request) has been registered '
                           'for this thread'):
            # This happens when this code gets called as part of a paster
            # command rather then as part of an HTTP request.
            current_lang = toolkit.config.get('ckan.locale_default')
        else:
            raise

    # fallback to default locale if locale not in suported langs
    if current_lang not in lang_set:
        current_lang = toolkit.config.get('ckan.locale_default', 'en')
    # treat current lang differenly so remove from set
    lang_set.remove(current_lang)

    # add default query field(s)
    query_fields = 'text'

    # weight current lang more highly
    query_fields += ' title_%s^8 text_%s^4' % (current_lang, current_lang)

    for lang in lang_set:
        query_fields += ' title_%s^2 text_%s' % (lang, lang)

    search_params['qf'] = query_fields

    '''
    Unless the query is already being filtered by any type
    (either positively, or negatively), reduce to only display
    'dataset' type
    This is done because by standard all types are displayed, this
    leads to strange situations where e.g. harvest sources are shown
    on organization pages.
    TODO: fix issue https://github.com/ckan/ckan/issues/2803 in CKAN core
    '''
    fq = search_params.get('fq', '')
    if 'dataset_type:' not in fq:
        search_params.update({'fq': "%s +dataset_type:dataset" % fq})

    # remove colon followed by a space from q to avoid false negatives
    q = search_params.get('q', '')
    search_params['q'] = re.sub(r":\s", " ", q)

    return search_params


def _transform_package_dates(pkg_dict):
    if pkg_dict.get('issued'):
        pkg_dict['issued'] = _transform_datetime_to_isoformat(
            pkg_dict['issued'])
    if pkg_dict.get('modified'):
        pkg_dict['modified'] = _transform_datetime_to_isoformat(
            pkg_dict['modified'])
    for temporal in pkg_dict.get('temporals', []):
        if temporal.get('start_date'):
            temporal['start_date'] = _transform_datetime_to_isoformat(
                temporal['start_date'])
        if temporal.get('end_date'):
            temporal['end_date'] = _transform_datetime_to_isoformat(
                temporal['end_date'])
    for resource in pkg_dict.get('resources', []):
        if resource.get('issued'):
            resource['issued'] = _transform_datetime_to_isoformat(
                resource['issued'])
        if resource.get('modified'):
            resource['modified'] = _transform_datetime_to_isoformat(
                resource['modified'])


def _transform_datetime_to_isoformat(value):
    """derive isoformat from datepicker date format"""
    try:
        d = parse(value, dayfirst=True)
        return d.isoformat()
    except (TypeError, ParserError):
        return ""


def _transform_publisher(pkg_dict):
    publisher = pkg_dict.get('publisher')
    if publisher and not isinstance(publisher, dict):
        pkg_dict['publisher'] = json.loads(publisher)
