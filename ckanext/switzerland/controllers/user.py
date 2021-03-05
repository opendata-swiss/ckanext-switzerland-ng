# encoding: utf-8

import logging

from ckan.controllers.user import UserController
from ckan.common import c, request
from ckan.lib.base import render
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)


class OgdchUserController(UserController):
    """Override the user controller for ogdch
    """
    def index(self):
        c.q = request.params.get('q', '')
        c.organization = request.params.get('organization', None)
        c.role = request.params.get('role', None)
        c.order_by = request.params.get('order_by', 'name')
        context = {'user': c.user,
                   'auth_user_obj': c.userobj}
        data_dict = {'q': c.q,
                     'order_by': c.order_by,
                     'role': c.role,
                     'organization': c.organization}
        users = tk.get_action('user_list')(context, data_dict)
        userroles = tk.get_action('member_roles_list')(context, {'group_type': 'organization'})  # noqa
        organizations = tk.get_action('organization_list')(context, {})

        c.roles = [{'text': 'Role: all', 'value': ''}, {'text': 'Sysadmin', 'value': 'sysadmin'}]  # noqa
        c.roles.extend(list(userroles))
        c.organizations = [{'text': 'Organization: all', 'value': ''}]
        c.organizations.extend([{'text': organization, 'value': organization}
                                for organization in organizations])
        c.page = {
            'users': users,
        }
        return render('user/list.html')
