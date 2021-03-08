# encoding: utf-8

import logging
import re

from ckan import authz
from ckan.controllers.user import UserController
from ckan.common import c, request, config, _
from ckan.lib.base import render
import ckan.plugins.toolkit as tk
from ckanext.switzerland.helpers.frontend_helpers import get_localized_value_for_display  # noqa

log = logging.getLogger(__name__)


class OgdchUserController(UserController):
    """Override the user controller to allow custom user search
    by organization and role.
    """
    def index(self):
        c.q = request.params.get('q', '')
        c.organization = request.params.get('organization', None)
        c.role = request.params.get('role', None)
        c.order_by = request.params.get('order_by', 'name')
        page_size = int(
            request.params.get('limit', config.get('ckan.user_list_limit', 20))
        )
        context = {'user': c.user,
                   'auth_user_obj': c.userobj}
        data_dict = {'q': c.q,
                     'order_by': c.order_by,
                     'role': c.role,
                     'organization': c.organization}

        try:
            tk.check_access('user_list', context, data_dict)
        except tk.NotAuthorized:
            tk.abort(403, _('Not authorized to see this page'))

        users = tk.get_action('ogdch_user_list')(context, data_dict)
        organization_tree = tk.get_action('group_tree')(context, {'type': 'organization'})  # noqa
        userroles = tk.get_action('member_roles_list')(context, {'group_type': 'organization'})  # noqa
        user_admin_organizations = tk.get_action('ogdch_get_admin_organizations_for_user')(context, {})  # noqa

        c.pagination = _get_pagination(request, len(users), page_size)
        c.roles = _get_role_selection(c.user, userroles)
        c.organizations = _get_organization_selection(organization_tree, user_admin_organizations)  # noqa

        c.page = {
            'users': users[c.pagination.get('offset', 0):c.pagination.get('offset', 0) + page_size],  # noqa
        }
        return render('user/list.html')


def _get_role_selection(current_user, userroles):
    """get selection of roles"""
    userroles_display = [{'text': 'Role: all', 'value': ''}]  # noqa
    if authz.is_sysadmin(current_user):
        userroles_display.append({'text': 'Sysadmin', 'value': 'sysadmin'})
    userroles_display.extend(list(userroles))
    return userroles_display


def _get_organization_selection(organization_tree, allowed_organizations):
    """get selection of organizations"""
    if not allowed_organizations:
        return []
    organizations_display = [{'text': 'Organization: all', 'value': ''}]  # noqa
    for organization in organization_tree:
        if organization['name'] in allowed_organizations:
            organizations_display.append(_prepare_organization_select_item(organization))  # noqa
        for suborganization in organization.get('children'):
            if suborganization['name'] in allowed_organizations:
                organizations_display.append(_prepare_organization_select_item(suborganization, is_suborganization=True))  # noqa
    return organizations_display


def _prepare_organization_select_item(organization, is_suborganization=False):
    """format select item for one organization"""
    organization_text = get_localized_value_for_display(organization.get('title'))  # noqa
    if is_suborganization:
        organization_text = "-" + organization_text
    return {'text': organization_text,
            'value': organization.get('name')}


def _get_pagination(request, count, page_size):
    """set up pagination"""
    try:
        current = int(request.params.get('page'))
    except Exception:
        current = 1
    total = count / page_size + 1
    offset = (current - 1) * page_size
    if "page" in tk.request.url:
        pagination_base_url = re.sub(r"page=\d", "page=", tk.request.url)
    elif '?' not in tk.request.url:
        pagination_base_url = tk.request.url + "?page="
    else:
        pagination_base_url = tk.request.url + "&page="
    return {
        'current': current,
        'total': total,
        'offset': offset,
        'base_url': pagination_base_url
    }
