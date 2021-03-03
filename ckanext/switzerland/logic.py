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
from ckan import authz
from ckan.lib.search.common import make_connection
import ckan.lib.plugins as lib_plugins
import ckan.lib.uploader as uploader
from ckan.logic.action.get import user_list as core_user_list
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

CAPACITY_ADMIN = 'admin'


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

    # Don't use uploader.get_uploader(), as this will return the S3Uploader.
    # We want to process the file locally and then delete it.
    upload = uploader.Upload('dataset_xml')
    upload.update_data_dict(data, 'dataset_xml',
                            'file_upload', 'clear_upload')
    upload.upload()
    dataset_filename = data.get('dataset_xml')

    if not dataset_filename:
        h.flash_error('Error uploading file.')
        return

    full_file_path = os.path.join(upload.storage_path, dataset_filename)
    data_rdfgraph = rdflib.ConjunctiveGraph()
    profile = SwissDCATAPProfile(data_rdfgraph)

    try:
        data_rdfgraph.parse(full_file_path, "xml")
    except Exception as e:
        h.flash_error(
            'Error parsing the RDF file during dataset import: {0}'
            .format(e))
        os.remove(full_file_path)
        return

    for dataset_ref in data_rdfgraph.subjects(RDF.type, DCAT.Dataset):
        dataset_dict = {}
        profile.parse_dataset(dataset_dict, dataset_ref)
        dataset_dict['owner_org'] = org_id

        _create_or_update_dataset(dataset_dict)

    # Clean up the file as we have no further use for it.
    os.remove(full_file_path)


@side_effect_free
def ogdch_showcase_search(context, data_dict):
    '''
    Custom package_search logic restricted to showcases, with 'for_view'=True
    so that the ckanext-showcase before_view method is called. This includes
    the number of datasets in each showcase in the output.
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context.update({'user': user['name'], 'for_view': True})

    if data_dict['fq']:
        data_dict['fq'] += ' dataset_type:showcase'
    else:
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

        try:
            tk.get_action('package_create')(context, dataset)
        except ValidationError as e:
            h.flash_error(
                'Error importing dataset %s: %r' %
                (dataset.get('name', ''), e.error_summary))

            return

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
    If only group_id is given, all non-sysadmin users
    will be added as members to that group
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
        return 'Added user "%s" to "%s".' % (user_id, group_id)
    elif user_id:
        _add_member_to_groups(user_id, context)
        return 'Added user %s to all available groups.' % user_id
    elif group_id:
        _add_members_to_group(group_id, context)
        return 'Added all non-admin users as members to group %s.' % group_id
    else:
        members = tk.get_action('user_list')(context, {})
        groups = tk.get_action('group_list')(context, {})
        for member in members:
            if not member['sysadmin']:
                for group in groups:
                    _add_member_to_group(member.get('id'), group, context)

        return 'Added all non-admin users as members to all available groups.'


def _add_members_to_group(group, context):
    members = tk.get_action('user_list')(context, {})
    for member in members:
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


@side_effect_free
def ogdch_get_admin_organizations_for_user(context, data_dict):
    '''
    Get list of organization where a user is admin of
    '''
    organizations_for_user = tk.get_action('organization_list_for_user')(context, data_dict)  # noqa
    organizations_where_user_is_admin = [
        organization.get('name')
        for organization in organizations_for_user
        if organization.get('capacity') == CAPACITY_ADMIN
    ]
    return organizations_where_user_is_admin


@side_effect_free
def ogdch_get_roles_for_user(context, data_dict):
    '''
    Get list of roles that a user has in organizations
    Roles in suborganizations are only included if they differ from the role in the
    top level organization
    '''
    organizations_for_user = tk.get_action('organization_list_for_user')(context, data_dict)  # noqa
    organizations = [organization.get('name')
                     for organization in organizations_for_user]
    userroles = [{'organization': organization.get('name'), 'role': organization.get('capacity')}  # noqa
                 for organization in organizations_for_user]

    organization_trees = []
    for organization in organizations:
        if not _check_organization_in_organization_trees(organization, organization_trees):  # noqa
            organization_tree = tk.get_action('group_tree_section')(
                context, {'type': 'organization', 'id': organization})  # noqa
            userroles = _check_userrole_in_organization_tree(userroles, organization_tree)  # noqa
            organization_trees.append(organization_tree)

    return userroles


def _check_organization_in_organization_trees(organization, organization_trees):
    """checks if a organization is in an organization tree"""
    for organization_tree in organization_trees:
        if organization == organization_tree.get('name'):
            return True
        suborganisations = organization_tree.get('children')
        if organization in [suborg.get('name') for suborg in suborganisations]:  # noqa
            return True
    return False


def _check_userrole_in_organization_tree(userroles, organization_tree):
    """returns userroles that a user has in organizations:
    roles in suborganizations are only included if they differ from the role in
    the top level organization"""
    top_organization = organization_tree.get('name')
    sub_organization_tree = organization_tree.get('children')
    if not sub_organization_tree:
        return userroles
    sub_organizations = [suborg.get('name') for suborg in sub_organization_tree]  # noqa
    userrole_organizations = [role['organization'] for role in userroles]
    if top_organization not in userrole_organizations:
        return userroles
    top_role = _get_role_from_userroles_for_organization(userroles, top_organization)  # noqa
    for suborg in sub_organizations:
        if suborg in userrole_organizations:
            suborg_role = _get_role_from_userroles_for_organization(userroles, suborg)  # noqa
            if suborg_role and suborg_role == top_role:
                userroles = _remove_role_from_userroles(userroles, suborg)
    return userroles


def _get_role_from_userroles_for_organization(userroles, organization):
    """gets the role of a user in an organization in the userrole list"""
    role_in_org = [role['role'] for role in userroles if role['organization'] == organization]  # noqa
    if role_in_org:
        return role_in_org[0]
    return None


def _remove_role_from_userroles(userroles, organization):
    """remove the role from the userroles list"""
    return [role for role in userroles if role['organization'] != organization]


@side_effect_free
def ogdch_get_users_with_organizations(context, data_dict):
    organization_list = tk.get_action('organization_list')(context, data_dict)
    users_with_organizations = {}
    for organization in organization_list:
        members = tk.get_action('member_list')(
            {'ignore_auth': True}, {'id': organization, 'object_type': 'user'})
        for member in members:
            user = member[0]
            if user in users_with_organizations:
                users_with_organizations[user].append(organization)
            else:
                users_with_organizations[user] = [organization]
    return users_with_organizations


@side_effect_free
def ogdch_user_list(context, data_dict):
    current_user = context.get('user')
    sysadmin = authz.is_sysadmin(current_user)
    user_list = core_user_list(context, data_dict)

    if sysadmin:
        return user_list

    user_list_with_organizations = tk.get_action('ogdch_get_users_with_organizations')(context, data_dict)  # noqa
    user_organization_dict = {id: user_list_with_organizations[id]
                              for id in user_list_with_organizations}
    admin_organizations_for_user = tk.get_action('ogdch_get_admin_organizations_for_user')(context, data_dict)  # noqa

    if admin_organizations_for_user:
        user_list_for_organization_admin = []
        for user in user_list:
            if not user.get('sysadmin'):
                user_organization_in_administered_organisations = \
                    [org for org in user_organization_dict.get(user['id'], [])
                     if org in admin_organizations_for_user]
                if user_organization_in_administered_organisations:
                    user_list_for_organization_admin.append(user)
        return user_list_for_organization_admin

    current_user_only = [user for user in user_list if user['name'] == current_user]  # noqa
    return current_user_only
