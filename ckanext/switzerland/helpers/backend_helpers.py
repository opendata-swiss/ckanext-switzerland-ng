# coding=UTF-8

"""
Helpers belong in this file if they are only
used in backend templates
"""
import ast
import logging
import re
import requests
from urlparse import urlparse
from html.parser import HTMLParser
from ckan import authz
from ckan.common import _, g, c
from ckan.lib.helpers import _link_to, lang, url_for
from ckan.lib.helpers import dataset_display_name as dataset_display_name_orig
from ckan.lib.helpers import organization_link as organization_link_orig

import ckan.lib.i18n as i18n
import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckanext.switzerland.helpers.localize_utils as ogdch_localize_utils
from ckanext.switzerland.helpers.frontend_helpers import get_localized_value_for_display  # noqa
from ckanext.harvest.helpers import harvester_types
from ckanext.hierarchy.helpers import group_tree

log = logging.getLogger(__name__)

OGDCH_USER_VIEW_CHOICE = 'user_view_choice'
OGDCH_USER_VIEW_CHOICE_FRONTEND = 'frontend'
OGDCH_USER_VIEW_CHOICE_BACKEND = 'backend'
REGEX_LANGUAGE_DICT = r'\{[\w\\\d\-\(\)\'\"\:\,\s]*\}'
CAPACITY_ADMIN = "admin"

showcase_types_mapping = {
    "application": u'{"fr": "Application", "de": "Applikation", "en": "Application", "it": "Applicazione"}', # noqa
    "data_visualization": u'{"fr": "Visualisation de donées", "de": "Daten-Visualisierung", "en": "Data visualization", "it": "Visualizzazione di dati"}', # noqa
    "event": u'{"fr": "Evènement", "de": "Veranstaltung", "en": "Event", "it": "Manifestazione"}', # noqa
    "blog_and_media_articles": u'{"fr": "Article blogs et médias", "de": "Blog und Medienartikel", "en": "Blog and media article", "it": "Blog/articolo"}', # noqa
    "paper": u'{"fr": "Article scientifique", "de": "Wissenschaftliche Arbeit", "en": "Paper", "it": "Articolo scientifico"}', # noqa
    "best_practice": u'{"fr": "Best practice", "de": "Best practice", "en": "Best practice", "it": "Best practice"}', # noqa
}


def ogdch_template_helper_get_active_class(active_url, section):
    """template helper: determines whether a link is an"""
    active_path = urlparse(active_url).path
    try:
        active_section = active_path.split('/')[1]
        if active_section == section:
            return 'active'
    except Exception:
        pass
    return ''


def create_showcase_types():
    """
    Create tags and vocabulary for showcase types, if they don't exist already.
    """
    user = tk.get_action("get_site_user")({"ignore_auth": True}, ())
    context = {"user": user["name"]}
    try:
        data = {"id": "showcase_types"}
        tk.get_action("vocabulary_show")(context, data)
        log.info("'showcase_types' vocabulary already exists, skipping")
    except TypeError as err:
        if err.message == ('No object (name: translator) has been registered '
                           'for this thread'):
            # This happens because the CKAN core translation function does not
            # yet default to the Flask one, so when this method is called
            # under some circumstances, the tk.ObjectNotFound error we are
            # expecting cannot be translated and throws a TypeError instead.
            # We should try removing this workaround when we upgrade to CKAN
            # v2.9.
            log.info("Creating vocab 'showcase_types'")
            data = {"name": "showcase_types"}
            vocab = tk.get_action("vocabulary_create")(context, data)
            for tag in showcase_types_mapping.keys():
                log.info(
                    "Adding tag {0} to vocab 'showcase_types'".format(tag)
                )
                data = {"name": tag, "vocabulary_id": vocab["id"]}
                tk.get_action("tag_create")(context, data)
        else:
            raise

    except tk.ObjectNotFound:
        log.info("Creating vocab 'showcase_types'")
        data = {"name": "showcase_types"}
        vocab = tk.get_action("vocabulary_create")(context, data)
        for tag in showcase_types_mapping.keys():
            log.info("Adding tag {0} to vocab 'showcase_types'".format(tag))
            data = {"name": tag, "vocabulary_id": vocab["id"]}
            tk.get_action("tag_create")(context, data)


def showcase_types():
    """
    Return the list of showcase types from the showcase_types vocabulary.
    """
    create_showcase_types()
    try:
        showcase_types = tk.get_action("tag_list")(
            data_dict={"vocabulary_id": "showcase_types"}
        )
        return showcase_types
    except tk.ObjectNotFound:
        return None


def get_showcase_type_name(showcase_type, lang_code):
    type_string = showcase_types_mapping.get(showcase_type, showcase_type)
    return ogdch_localize_utils.get_localized_value_from_json(
        type_string,
        lang_code
    )


def localize_showcase_facet_title(facet_item):
    return get_showcase_type_name(
        facet_item['display_name'],
        lang_code=lang()
    )


def localize_harvester_facet_title(facet_item):
    for type in harvester_types():
        if type['value'] == facet_item['name']:
            return type['text']

    return facet_item['display_name']


def group_id_in_groups(group_id, groups):
    for group in groups:
        if group_id == group['id']:
            return True
    return False


def get_localized_group_list(lang_code):
    """
    Returns a list of dicts containing the id, name and localized title
    for each group.
    """
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    groups = tk.get_action('group_list')(req_context, {'all_fields': True})
    group_list = []
    for group in groups:
        group_list.append({
            'id': group['id'],
            'name': group['name'],
            'title': ogdch_localize_utils.get_localized_value_from_json(
                group['title'],
                lang_code
            ),
        })

    group_list.sort(key=lambda group: ogdch_localize_utils.strip_accents(group['title'].lower()), reverse=False)  # noqa
    return group_list


def ogdch_get_organization_field_list(field):
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    orgs = tk.get_action('organization_list')(
        req_context,
        {'all_fields': True}
    )

    return [{'value': org['name'], 'label': ogdch_localize_utils.get_localized_value_from_json( # noqa
        org['title'],
        i18n.get_lang()
    )} for org in orgs]


def ogdch_get_political_level_field_list(field):
    return [
        {'label': _('Confederation'), 'value': 'confederation'},
        {'label': _('Canton'), 'value': 'canton'},
        {'label': _('Commune'), 'value': 'commune'},
        {'label': _('Other'), 'value': 'other'},
    ]


def ogdch_resource_display_name(res):
    """
    monkey patched version of ckan.lib.helpers.resource_display_name which
    extracts the correct translation of the dataset name, and substitutes the
    package title if there is no resource name
    """
    resource_display_name = get_localized_value_for_display(res.get('name'))
    if not resource_display_name:
        try:
            pkg = logic.get_action('package_show')(
                {}, {'id': res['package_id']}
            )
            resource_display_name = get_localized_value_for_display(
                pkg.get('title')
            )
            if not resource_display_name:
                return pkg['name']
        except (logic.NotFound, logic.ValidationError,
                logic.NotAuthorized, AttributeError):
            return ""
    return resource_display_name


def dataset_display_name(package_or_package_dict):
    """
    monkey patched version of ckan.lib.helpers.dataset_display_name which
    extracts the correct translation of the dataset name
    """
    name = dataset_display_name_orig(package_or_package_dict)
    return get_localized_value_for_display(name)


def organization_link(organization):
    """
    monkey patched version of ckan.lib.helpers.organization_link which extracts
    the correct translation of the organization name
    """
    organization['title'] = get_localized_value_for_display(
        organization['title'])
    return organization_link_orig(organization)


def group_link(group):
    """
    monkey patched version of ckan.lib.helpers.group_link which extracts the
    correct translation of the group title
    """
    url = url_for(controller='group', action='read', id=group['name'])
    title = group['title']
    try:
        # The group creation message contains str(dict), so we must parse the
        # string with literal_eval to fix it. If the title is really just a
        # string, a ValueError is thrown.
        title = ast.literal_eval(title)
        title = get_localized_value_for_display(title)
    except ValueError:
        pass

    link = _link_to(title, url)
    try:
        # Sometimes the title has special characters encoded as unicode_escape
        # (e.g. '\u00e9'). Sometimes they are already decoded (e.g. 'é').
        link = link.decode('unicode_escape')
    except UnicodeEncodeError:
        pass
    return link


def resource_link(resource_dict, package_id):
    """
    monkey patched version of ckan.lib.helpers.resource_link which extracts the
    correct translation of the resource name
    """
    if 'name' in resource_dict and resource_dict['name']:
        resource_dict['name'] = get_localized_value_for_display(
            ast.literal_eval(resource_dict['name']))

    text = ogdch_resource_display_name(resource_dict)
    url = url_for(controller='package',
                  action='resource_read',
                  id=package_id,
                  resource_id=resource_dict['id'])
    return _link_to(text, url)


def ogdch_get_top_level_organisations():
    """
    get the top level organisations as parent choices for suborganisations
    """
    try:
        parent_organizations = group_tree(type_='organization')
        return parent_organizations
    except tk.ObjectNotFound:
        return []


def ogdch_user_datasets():
    context = {u'for_view': True, u'user': g.user, u'auth_user_obj': g.userobj}
    data_dict = {u'user_obj': g.userobj, u'include_datasets': True}
    user_dict = logic.get_action(u'user_show')(context, data_dict)

    return user_dict['datasets']


def ogdch_localize_activity_item(msg):
    """localizing activity messages: this function gets an html message and
    replaces the language dict in there with the localized value
    """
    parser = HTMLParser()
    unescaped_msg = parser.unescape(msg)

    language_dict_result = re.search(REGEX_LANGUAGE_DICT, unescaped_msg)
    if not language_dict_result:
        return tk.literal(msg)

    language_dict = language_dict_result.group(0)
    localized_language_dict = get_localized_value_for_display(language_dict)
    localized_msg = unescaped_msg.replace(
        language_dict, localized_language_dict
    )
    return tk.literal(localized_msg)


def ogdch_admin_capacity():
    """tests whether the current user is a sysadmin
    or an organization admin
    """
    if authz.is_sysadmin(c.user):
        return True
    context = {"user": c.user, "auth_user_obj": c.userobj}
    roles_for_user = tk.get_action("organization_list_for_user")(
        context, {"id": c.user}
    )
    capacities = [role.get("capacity") for role in roles_for_user]
    if CAPACITY_ADMIN in capacities:
        return True
    return False


def ogdch_get_switch_connectome_url(identifier):
    """Construct a url to the SWITCH connectome site using the id of a package
    on opendata.swiss. The connectome site only uses package ids from the PROD
    site, which are different from ids on TEST.

    This helper is only needed temporarily for a proof of concept: the
    connectome website should use dataset identifiers in the future, not ids.
    """
    permalink = "%s/api/3/action/ogdch_dataset_by_identifier?identifier=%s" % (
        tk.config.get("ckanext.switzerland.prod_env_url", ""),
        identifier,
    )
    r = requests.get(permalink)

    if r.status_code == 200 and r.json().get("result"):
        prod_id = r.json()["result"]["id"]

        return (
                tk.config.get(
                    "ckanext.switzerland.switch_connectome_base_url", ""
                )
                + prod_id
        )

    return ""
