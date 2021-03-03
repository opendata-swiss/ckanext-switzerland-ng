# encoding: utf-8

import logging

from ckan.controllers.user import UserController
from ckan.common import c
from ckan.lib.base import render
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)


class OgdchUserController(UserController):
    """Override the user controller for ogdch
    """
    def index(self):
        context = {'user': c.user,
                   'auth_user_obj': c.userobj}
        users = tk.get_action('user_list')(context, {})
        c.page = {
            'users': users,
        }
        return render('user/list.html')
