# encoding: utf-8

import logging

from ckan.controllers.user import UserController
import ckan.lib.helpers as h
from ckan.common import _, c, request, response, config
from ckan.lib.base import render, abort
from ckan.logic import get_action, NotAuthorized
from ckan import model, authz
from ckan.lib.navl.validators import not_empty
from ckanext.switzerland.helpers.frontend_helpers import ogdch_group_tree

log = logging.getLogger(__name__)

class OgdchUserController(UserController):
    """Override the user controller for ogdch
    """
    new_user_form = 'user/register.html'

    def index(self):
        page = h.get_page_number(request.params)
        c.q = request.params.get('q', '')
        c.order_by = request.params.get('order_by', 'name')

        context = {'return_query': True, 'user': c.user,
                   'auth_user_obj': c.userobj}

        data_dict = {'q': c.q,
                     'order_by': c.order_by}

        limit = int(
            request.params.get('limit', config.get('ckan.user_list_limit', 20))
        )
        try:
            h.check_access('user_list', context)
        except NotAuthorized:
            abort(403, _('Not authorized to see this page'))

        users_list = get_action('user_list')(context, data_dict)

        c.page = h.Page(
            collection=users_list,
            page=page,
            url=h.pager_url,
            item_count=users_list.count(),
            items_per_page=limit
        )
        return render('user/list.html')
