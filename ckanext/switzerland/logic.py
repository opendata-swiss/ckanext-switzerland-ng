from collections import OrderedDict
import datetime
import os.path
import pysolr
import re
from unidecode import unidecode
import uuid

import rdflib
import rdflib.parser
from rdflib.namespace import Namespace, RDF
from ratelimit import limits

from ckan.common import config
from ckan.plugins.toolkit import get_or_bust, side_effect_free
from ckan.logic import ActionError, NotFound, ValidationError
import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
from ckan.lib.search.common import make_connection
import ckan.lib.plugins as lib_plugins
import ckan.lib.uploader as uploader
from ckan.logic import check_access
from ckan.logic.action.create import user_create as core_user_create
from ckanext.dcatapchharvest.profiles import SwissDCATAPProfile
from ckanext.dcatapchharvest.harvesters import SwissDCATRDFHarvester
from ckanext.harvest.model import HarvestJob
from ckanext.harvest.logic.dictization import harvest_job_dictize
from ckanext.switzerland.helpers.request_utils import get_content_headers
from ckanext.switzerland.helpers.mail_helper import (
    send_registration_email,
    send_showcase_email)
from ckanext.switzerland.helpers.logic_helpers import (
    get_dataset_count, get_org_count, get_showcases_for_dataset,
    map_existing_resources_to_new_dataset)
from ckan.lib.munge import munge_title_to_name
from ckanext.subscribe.email_auth import authenticate_with_code
from ckanext.subscribe.action import (subscribe_list_subscriptions,
                                      subscribe_unsubscribe,
                                      subscribe_unsubscribe_all)

import logging

log = logging.getLogger(__name__)

FORMAT_TURTLE = 'ttl'
DATA_IDENTIFIER = 'data'
RESULT_IDENTIFIER = 'result'
HARVEST_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
HARVEST_STATUS_RUNNING = "Running"

DCAT = Namespace("http://www.w3.org/ns/dcat#")
FIVE_MINUTES = 300


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


@limits(calls=2, period=FIVE_MINUTES)
def ogdch_showcase_submit(context, data_dict):
    '''
    Custom logic to create a showcase. Showcases can be submitted
    from the frontend and should be created in one step along with
    all the datasets that are attached to the showcase.
    '''
    try:
        title = data_dict.get('title')
        if not title:
            raise ValidationError("Missing title value")
        data_dict['name'] = munge_title_to_name(title)
        showcase = tk.get_action('ckanext_showcase_create')(
            context, data_dict
        )
        package_association_data_dict = {'showcase_id': showcase['id']}
        datasets = data_dict.get('datasets')
        if datasets:
            for package_id in datasets:
                package_association_data_dict['package_id'] = package_id
                tk.get_action('ckanext_showcase_package_association_create')(
                    context, package_association_data_dict
                )
        return showcase
    except ValidationError:
        raise


@side_effect_free
def ogdch_harvest_monitor(context, data_dict):
    """Returns the status of the fetch and gather processes.

    If there are still-running harvest jobs that were created more than
    6 hours ago, it is likely that either of those processes has stopped
    and needs to be restarted, so we return result["ok"] = False and a list
    of long-running jobs.
    """

    check_access("harvest_job_list", context, data_dict)
    session = context["session"]
    query = (
        session.query(HarvestJob)
        .filter(HarvestJob.status == HARVEST_STATUS_RUNNING)
        .order_by(HarvestJob.created.desc())
    )

    jobs = query.all()

    now = datetime.datetime.now()
    six_hours = datetime.timedelta(hours=6)
    long_jobs = []
    result = {}

    for job in jobs:
        if now - job.created > six_hours:
            long_jobs.append(job)

    result["ok"] = len(long_jobs) == 0

    context["return_error_summary"] = False
    result["long_running_jobs"] = [
        harvest_job_dictize(job, context) for job in long_jobs
    ]

    return result


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


def ogdch_user_create(context, data_dict):
    """overwrites the core user creation to send an email
    to new users"""
    user = core_user_create(context, data_dict)
    tk.get_action('ogdch_add_users_to_groups')(
        context, {'user_id': user['id']}
    )
    send_email_on_registration = tk.asbool(config.get(
        'ckanext.switzerland.send_email_on_user_registration', True
    ))

    if not(send_email_on_registration and user.get('email')):
        return user

    success = False
    exception = ''
    try:
        send_registration_email(user)
        success = True
    except Exception as e:
        exception = e

    try:
        if success:
            h.flash_success("An email has been sent to the user {} at {}."
                            .format(user['name'], user['email']))
        else:
            message = "The email could not be sent to {} for user {}.".format(
                user['email'], user['name'])
            if exception:
                message += " An error occured: {}".format(exception)
            h.flash_error(message)
    except TypeError:
        # We get this error when creating a user via the command line.
        # Then there is no session, so showing a flash message fails.
        log.warning(
            "The email could not be sent to {} for user {}."
            " An error occured: {}"
            .format(user['email'], user['name'], exception))

    return user


def ogdch_showcase_create(context, data_dict):
    '''Custom showcase creation so that a notification
    can be sent when a showcase is created.'''
    data_dict['type'] = 'showcase'

    upload = uploader.get_uploader('showcase')

    upload.update_data_dict(data_dict, 'image_url',
                            'image_upload', 'clear_upload')

    upload.upload(uploader.get_max_image_size())

    showcase = tk.get_action('package_create')(context, data_dict)
    try:
        send_showcase_email(showcase)
    except Exception as e:
        log.error(
            "Sending a notification when a showcase was created"
            " received an exception: {}"
           .format(e))
    return showcase


def _get_email_from_subscribe_code(code):
    """Get the email address of a subscription from an auth code.
    """
    try:
        email = authenticate_with_code(code)
    except ValueError:
        raise ValidationError("Code is not valid")

    if not email:
        raise Exception("The email is not valid")

    return email


def ogdch_subscribe_manage(context, data_dict):
    """Get an email address from a given auth code, and then return
    information about existing subscriptions for that email address.
    :returns: list of dictionaries
    """
    data_dict['email'] = _get_email_from_subscribe_code(data_dict['code'])

    return subscribe_list_subscriptions(context, data_dict)


def ogdch_subscribe_unsubscribe(context, data_dict):
    """Get an email address from a given auth code, and then unsubscribe that
    email address from notifications for a given dataset.

    :returns: (object_name, object_type) where object_type is: dataset, group
        or organization (but we are only offering dataset subscriptions on the
        frontend, so it will be dataset)
    """
    data_dict['email'] = _get_email_from_subscribe_code(data_dict['code'])

    return subscribe_unsubscribe(context, data_dict)


def ogdch_subscribe_unsubscribe_all(context, data_dict):
    """Get an email address from a given auth code, and then unsubscribe
    that email address from all notifications.

    :returns: None
    """
    data_dict['email'] = _get_email_from_subscribe_code(data_dict['code'])

    return subscribe_unsubscribe_all(context, data_dict)
