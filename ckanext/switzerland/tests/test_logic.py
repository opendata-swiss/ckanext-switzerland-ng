# encoding: utf-8
import logging
import nose

import ckan.plugins.toolkit as tk
from ckanext.switzerland.tests import OgdchFunctionalTestBase

assert_dict_equal = nose.tools.assert_dict_equal
assert_equal = nose.tools.assert_equal
assert_not_equal = nose.tools.assert_not_equal
assert_true = nose.tools.assert_true
log = logging.getLogger(__name__)


class TestForceResetPasswords(OgdchFunctionalTestBase):
    def setup(self):
        super(TestForceResetPasswords, self).setup()
        for n in range(3):
            user = {
                "name": "user{}".format(str(n)),
                "email": "user{}@example.org".format(str(n)),
                "password": "password{}".format(str(n)),
            }
            tk.get_action("user_create")(self._get_context(), user)

    def test_reset_single_user_password(self):
        initial_user = tk.get_action("user_show")(
            self._get_context(),
            {"id": "user0", "include_password_hash": True}
        )

        initial_other_user_passwords = {}
        for user in ["user1", "user2", "default"]:
            initial_other_user_passwords[user] = tk.get_action("user_show")(
                self._get_context(),
                {"id": user, "include_password_hash": True}
            )["password_hash"]

        context = self._get_context()
        context["ignore_auth"] = False
        tk.get_action("ogdch_force_reset_passwords")(
            context, {"user": "user0", "notify": False}
        )

        updated_user = tk.get_action("user_show")(
            self._get_context(),
            {"id": "user1", "include_password_hash": True}
        )
        other_user_passwords_after_reset = {}
        for user in ["user1", "user2", "default"]:
            other_user_passwords_after_reset[user] = tk.get_action("user_show")(
                self._get_context(),
                {"id": user, "include_password_hash": True}
            )["password_hash"]

        assert_not_equal(
            updated_user["password_hash"],
            initial_user["password_hash"],
            "User password should have been updated"
        )
        assert_dict_equal(
            initial_other_user_passwords,
            other_user_passwords_after_reset,
            "Other users' passwords should not have been changed"
        )

