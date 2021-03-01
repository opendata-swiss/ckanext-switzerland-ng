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
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

class OgdchUserController(UserController):
    """Override the user controller for ogdch
    """
    def ogdchindex(self):
        c.myname = {'name': "Sabine"}
        context = {'user': c.user,
                   'auth_user_obj': c.userobj}
        result = tk.get_action('ogdch_user_list')(context, {})
        log.error(result)
        try:
            c.myresult = {'result': result}
        except Exception as e:
            c.exception = e
        return render('user/userlist.html')
