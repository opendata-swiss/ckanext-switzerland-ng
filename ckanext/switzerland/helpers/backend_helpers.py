# coding=UTF-8

"""
Helpers belong in this file if they are only
used in backend templates
"""
import logging
from urlparse import urlparse
from ckan.common import session
from ckan.authz import auth_is_loggedin_user
from ckan.common import _
import ckan.lib.i18n as i18n
import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckanext.switzerland.helpers.localize_utils as ogdch_localize_utils
from ckanext.switzerland.helpers.frontend_helpers import get_localized_value_for_display  # noqa

log = logging.getLogger(__name__)

OGDCH_USER_VIEW_CHOICE = 'user_view_choice'
OGDCH_USER_VIEW_CHOICE_FRONTEND = 'frontend'
OGDCH_USER_VIEW_CHOICE_BACKEND = 'backend'

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


def ogdch_template_choice(template_frontend, template_backend):
    """decides whether to return a frontend
    or a backend template"""
    logged_in = auth_is_loggedin_user()
    if not logged_in:
        return template_frontend
    session_frontend = session \
        and OGDCH_USER_VIEW_CHOICE in session.keys() \
        and (session[OGDCH_USER_VIEW_CHOICE] == OGDCH_USER_VIEW_CHOICE_FRONTEND) # noqa
    if session_frontend:
        return template_frontend
    else:
        return template_backend


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
    resource_display_name = res.get('name')
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


def ogdch_add_users_to_groups(user_id=None, group_id=None):
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

    if user_id and group_id:
        _add_member_to_group(user_id, group_id, context)
    elif user_id:
        _add_member_to_groups(user_id, context)
    elif group_id:
        _add_members_to_group(group_id, context)


def _add_members_to_group(group, context):
    members = tk.get_action('user_list')(context, {})
    for member in members:
        # sysadmins will keep their admin role, every other user will be added as a member
        if not member['sysadmin']:
            _add_member_to_group(member, group, context)


def _add_member_to_groups(member, context):
    groups = tk.get_action('group_list')(context, {})
    for group in groups:
        _add_member_to_group(member, group)


def _add_member_to_group(member, group, context):
    update_group_members_dict = {
        'id': group,
        'username': member['id'],
        'role': 'member',
    }
    tk.get_action('group_member_create')(context, update_group_members_dict)