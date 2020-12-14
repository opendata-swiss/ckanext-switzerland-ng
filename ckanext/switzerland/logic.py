from collections import OrderedDict
import os.path
import pysolr
import re
from unidecode import unidecode
import uuid
from xml.sax import SAXParseException

import rdflib
import rdflib.parser
from rdflib.namespace import Namespace, RDF

from ckan.plugins.toolkit import get_or_bust, side_effect_free
from ckan.logic import ActionError, NotFound, ValidationError
import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
from ckan.lib.search.common import make_connection
import ckan.lib.plugins as lib_plugins
import ckan.lib.uploader as uploader
from ckanext.dcat.processors import RDFParserException
from ckanext.dcatapchharvest.profiles import SwissDCATAPProfile
from ckanext.dcatapchharvest.harvesters import SwissDCATRDFHarvester
from ckanext.switzerland.helpers.request_utils import get_content_headers
from ckanext.switzerland.helpers.logic_helpers import (
    get_dataset_count, get_org_count, get_showcases_for_dataset,
    map_existing_resources_to_new_dataset)

import logging

log = logging.getLogger(__name__)

FORMAT_TURTLE = 'ttl'
DATA_IDENTIFIER = 'data'
RESULT_IDENTIFIER = 'result'

DCAT = Namespace("http://www.w3.org/ns/dcat#")


@side_effect_free
def ogdch_counts(context, data_dict):
    '''
    Return the following data about our ckan instance:
    - total number of datasets
    - number of datasets per group
    - total number of showcases
    - total number of organisations (including all levels of the hierarchy)
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}

    # group_list contains the number of datasets in the 'packages' field
    groups = tk.get_action('group_list')(req_context, {'all_fields': True})
    group_count = OrderedDict()
    for group in groups:
        group_count[group['name']] = group['package_count']

    return {
        'total_dataset_count': get_dataset_count('dataset'),  # noqa
        'showcase_count': get_dataset_count('showcase'),  # noqa
        'groups': group_count,
        'organization_count': get_org_count(),
    }


@side_effect_free  # noqa
def ogdch_package_show(context, data_dict):  # noqa
    """
    custom package_show logic that returns a dataset together
    with related datasets, showcases and terms of use
    """
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context.update({'user': user['name'], 'for_view': True})
    id = get_or_bust(data_dict, 'id')

    result = tk.get_action('package_show')(context, {'id': id})
    if result:
        if result.get('see_alsos'):
            for item in result.get('see_alsos'):
                try:
                    related_dataset = tk.get_action('ogdch_dataset_by_identifier')(  # noqa
                        context, {'identifier': item.get('dataset_identifier')})  # noqa
                    if related_dataset:
                        item['title'] = related_dataset['title']
                        item['name'] = related_dataset['name']
                except:
                    continue

        try:
            showcases = get_showcases_for_dataset(id=id)
            result['showcases'] = showcases
        except:
            pass

        try:
            result['terms_of_use'] = tk.get_action('ogdch_dataset_terms_of_use')(  # noqa
                context, {'id': id})
        except:
            raise "Terms of Use could not be found for dataset {}".format(id)

        for resource in result['resources']:
            resource_views = tk.get_action('resource_view_list')(
                context, {'id': resource['id']})
            resource['has_views'] = len(resource_views) > 0

        return result
    else:
        raise tk.NotFound


@side_effect_free
def ogdch_content_headers(context, data_dict):
    '''
    Returns some headers of a remote resource
    '''
    url = get_or_bust(data_dict, 'url')
    response = get_content_headers(url)
    return {
        'status_code': response.status_code,
        'content-length': response.headers.get('content-length', ''),
        'content-type': response.headers.get('content-type', ''),
    }


@side_effect_free
def ogdch_dataset_terms_of_use(context, data_dict):
    '''
    Returns the terms of use for the requested dataset.

    By definition the terms of use of a dataset corresponds
    to the least open rights statement of all distributions of
    the dataset
    '''
    terms = [
        'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
        'NonCommercialAllowed-CommercialAllowed-ReferenceRequired',
        'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired',
        'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired',
        'ClosedData',
    ]
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    pkg_id = get_or_bust(data_dict, 'id')
    pkg = tk.get_action('package_show')(req_context, {'id': pkg_id})

    least_open = None
    for res in pkg['resources']:
        if 'rights' in res:
            if res['rights'] not in terms:
                least_open = 'ClosedData'
                break
            if least_open is None:
                least_open = res['rights']
                continue
            if terms.index(res['rights']) > terms.index(least_open):
                least_open = res['rights']

    if least_open is None:
        least_open = 'ClosedData'

    return {
        'dataset_rights': least_open
    }


@side_effect_free
def ogdch_dataset_by_identifier(context, data_dict):
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context.update({'user': user['name']})
    identifier = data_dict.pop('identifier', None)

    data_dict['fq'] = 'identifier:%s' % identifier
    result = tk.get_action('package_search')(context, data_dict)
    try:
        return result['results'][0]
    except (KeyError, IndexError, TypeError):
        raise NotFound


@side_effect_free
def ogdch_autosuggest(context, data_dict):
    q = get_or_bust(data_dict, 'q')
    lang = get_or_bust(data_dict, 'lang')
    fq = data_dict.get('fq', '')

    if fq:
        fq = 'NOT private AND %s' % fq
    else:
        fq = 'NOT private'

    # parse language from values like de_CH
    if len(lang) > 2:
        lang = lang[:2]

    if lang not in ['en', 'it', 'de', 'fr']:
        raise ValidationError('lang must be one of [en, it, de, fr]')

    handler = '/suggest_%s' % lang
    suggester = 'ckanSuggester_%s' % lang

    solr = make_connection()
    try:
        log.debug(
            'Loading suggestions for %s (lang: %s, fq: %s)' % (q, lang, fq)
        )
        results = solr.search(
            '',
            search_handler=handler,
            **{'suggest.q': q, 'suggest.count': 10, 'suggest.cfq': fq}
        )
        suggestions = results.raw_response['suggest'][suggester].values()[0]  # noqa

        def highlight(term, q):
            if '<b>' in term:
                return term
            clean_q = unidecode(q)
            clean_term = unidecode(term)

            re_q = re.escape(clean_q)
            m = re.search(re_q, clean_term, re.I)
            if m:
                replace_text = term[m.start():m.end()]
                term = term.replace(replace_text, '<b>%s</b>' % replace_text)
            return term

        terms = [highlight(suggestion['term'], q) for suggestion in suggestions['suggestions']]  # noqa
        return list(set(terms))
    except pysolr.SolrError as e:
        log.exception('Could not load suggestions from solr: %s' % e)
    raise ActionError('Error retrieving suggestions from solr')


def ogdch_xml_upload(context, data_dict):
    data = data_dict.get('data')
    org_id = data_dict.get('organization')

    upload = uploader.get_uploader('dataset_xml')
    upload.update_data_dict(data, 'dataset_xml',
                            'file_upload', 'clear_upload')
    upload.upload()

    dataset_filename = data.get('dataset_xml')

    if not dataset_filename:
        h.flash_error('Error uploading file.')
        return

    data_rdfgraph = rdflib.ConjunctiveGraph()
    profile = SwissDCATAPProfile(data_rdfgraph)

    try:
        data_rdfgraph.parse(os.path.join(
            upload.storage_path,
            dataset_filename
        ), "xml")
    except (RDFParserException, SAXParseException) as e:
        h.flash_error(
            'Error parsing the RDF file during dataset import: {0}'
            .format(e))

    for dataset_ref in data_rdfgraph.subjects(RDF.type, DCAT.Dataset):
        dataset_dict = {}
        profile.parse_dataset(dataset_dict, dataset_ref)
        dataset_dict['owner_org'] = org_id

        _create_or_update_dataset(dataset_dict)


@side_effect_free
def ogdch_showcase_search(context, data_dict):
    '''
    Custom package_search logic restricted to showcases, with 'for_view'=True
    so that the ckanext-showcase before_view method is called. This includes
    the number of datasets in each showcase in the output.
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context.update({'user': user['name'], 'for_view': True})
    data_dict.update({'fq': 'dataset_type:showcase'})

    result = tk.get_action('package_search')(context, data_dict)
    if result:
        return result
    else:
        raise NotFound


def _create_or_update_dataset(dataset):
    context = {}
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context.update({'user': user['name']})

    tk.check_access('package_show', {})

    harvester = SwissDCATRDFHarvester()
    name = harvester._gen_new_name(dataset['title'])

    package_plugin = lib_plugins.lookup_package_plugin('dataset')
    data_dict = {
        'identifier': dataset['identifier'],
        'include_private': True,
        'include_drafts': True,
    }

    try:
        existing_dataset = tk.get_action('ogdch_dataset_by_identifier')(
            context,
            data_dict
        )
        context['schema'] = package_plugin.update_package_schema()

        # Don't change the dataset name even if the title has changed
        dataset['name'] = existing_dataset['name']
        dataset['id'] = existing_dataset['id']
        # Don't make a dataset public if it wasn't already
        is_private = existing_dataset['private']
        dataset['private'] = is_private

        map_existing_resources_to_new_dataset(dataset, existing_dataset)

        tk.get_action('package_update')(context, dataset)

        success_message = 'Updated dataset %s.' % dataset['name']
        if is_private:
            success_message += ' The dataset visibility is private.'

        h.flash_success(success_message)

    except NotFound as e:
        package_schema = package_plugin.create_package_schema()
        context['schema'] = package_schema

        # We need to explicitly provide a package ID
        dataset['id'] = str(uuid.uuid4())
        package_schema['id'] = [str]
        dataset['name'] = name
        # Create datasets as private initially
        dataset['private'] = True

        tk.get_action('package_create')(context, dataset)

        h.flash_success(
            'Created dataset %s. The dataset visibility is private.' %
            dataset['name'])

    except Exception as e:
        h.flash_error(
            'Error importing dataset %s: %r' %
            (dataset.get('name', ''), e))


@side_effect_free
def ogdch_add_users_to_groups(context, data_dict={}):
    """
    If user_id and group_id is given, that user will be added to that group.
    If only user_id is given, they will be added to each group.
    If only group_id is given, all non-sysadmin users will be added as members to that group
    :param user_id: (optional, default: ``None``)
    :param group_id: (optional, default: ``None``)
    :return:
    """
    user = tk.get_action('get_site_user')({'ignore_auth': True}, ())
    context = {'user': user['name']}

    group_id = data_dict.get('group_id')
    user_id = data_dict.get('user_id')

    if user_id and group_id:
        _add_member_to_group(user_id, group_id, context)
        return 'Added user "' + user_id + '" to ' + group_id + '.'
    elif user_id:
        _add_member_to_groups(user_id, context)
        return 'Added user "' + user_id + '" to all available groups.'
    elif group_id:
        _add_members_to_group(group_id, context)
        return 'Added all non-admin users as members to group "' + group_id + '".'
    else:
        members = tk.get_action('user_list')(context, {})
        groups = tk.get_action('group_list')(context, {})
        for member in members:
            # sysadmins will keep their admin role, every other user will be added as a member
            if not member['sysadmin']:
                for group in groups:
                    _add_member_to_group(member.get('id'), group, context)

        return 'Added all non-admin users as members to all available groups.'


def _add_members_to_group(group, context):
    members = tk.get_action('user_list')(context, {})
    for member in members:
        # sysadmins will keep their admin role, every other user will be added as a member
        if not member['sysadmin']:
            _add_member_to_group(member.get('id'), group, context)


def _add_member_to_groups(member, context):
    groups = tk.get_action('group_list')(context, {})
    for group in groups:
        _add_member_to_group(member, group, context)


def _add_member_to_group(member, group, context):
    update_group_members_dict = {
        'id': group,
        'username': member,
        'role': 'member',
    }
    tk.get_action('group_member_create')(context, update_group_members_dict)
