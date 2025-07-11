# encoding: utf-8
import hashlib
import logging

import ckan.plugins.toolkit as tk
import nose
from ckan.plugins.toolkit import config
from ckan.tests.legacy.mock_mail_server import SmtpServerHarness

from ckanext.switzerland.tests.conftest import get_context

assert_dict_equal = nose.tools.assert_dict_equal
assert_equal = nose.tools.assert_equal
assert_in = nose.tools.assert_in
assert_not_equal = nose.tools.assert_not_equal

log = logging.getLogger(__name__)


class TestForceResetPasswords(SmtpServerHarness):
    site_user = ""

    @classmethod
    def setup_class(cls):
        super(TestForceResetPasswords, cls).setup_class()
        smtp_server = config.get("smtp.test_server")
        if smtp_server:
            host, port = smtp_server.split(":")
            port = int(port) + int(str(hashlib.md5(cls.__name__).hexdigest())[0], 16)
            config["smtp.test_server"] = f"{host}:{port}"
        SmtpServerHarness.setup_class()

    def setup(self):
        super(TestForceResetPasswords, self).setup()
        self.site_user = get_context()["user"]

        for n in range(3):
            user = {
                "name": f"user{str(n)}",
                "email": f"user{str(n)}@example.org",
                "password": f"password{str(n)}",
            }
            tk.get_action("user_create")(get_context(), user)

    @classmethod
    def teardown_class(cls):
        cls.smtp_thread.stop()
        SmtpServerHarness.teardown_class()

    def test_reset_single_user_password(self):
        initial_user = tk.get_action("user_show")(
            get_context(), {"id": "user0", "include_password_hash": True}
        )

        initial_other_user_passwords = {}
        for user in ["user1", "user2", self.site_user]:
            initial_other_user_passwords[user] = tk.get_action("user_show")(
                get_context(), {"id": user, "include_password_hash": True}
            )["password_hash"]

        context = get_context()
        context["ignore_auth"] = False
        result = tk.get_action("ogdch_force_reset_passwords")(
            context, {"user": "user0"}
        )

        updated_user = tk.get_action("user_show")(
            get_context(), {"id": "user1", "include_password_hash": True}
        )
        other_user_passwords_after_reset = {}
        for user in ["user1", "user2", self.site_user]:
            other_user_passwords_after_reset[user] = tk.get_action("user_show")(
                get_context(), {"id": user, "include_password_hash": True}
            )["password_hash"]

        assert_equal(
            ["user0"],
            result["success_users"],
            "Expected to receive a success message for resetting password",
        )
        assert_equal(
            {}, result["errors"], "No errors were expected for resetting password"
        )
        assert_not_equal(
            updated_user["password_hash"],
            initial_user["password_hash"],
            "User password should have been updated",
        )
        assert_dict_equal(
            initial_other_user_passwords,
            other_user_passwords_after_reset,
            "Other users' passwords should not have been changed",
        )

    def test_reset_multiple_user_passwords(self):
        initial_user_passwords = {}
        users = tk.get_action("user_list")(get_context(), {"all_fields": False})
        # We have four users: [u'default', u'user0', u'user1', u'user2']
        for user in users:
            initial_user_passwords[user] = tk.get_action("user_show")(
                get_context(), {"id": user, "include_password_hash": True}
            )["password_hash"]

        context = get_context()
        context["ignore_auth"] = False
        tk.get_action("ogdch_force_reset_passwords")(
            context, {"limit": "2", "offset": "1"}
        )

        user_passwords_after_update = {}
        for user in users:
            user_passwords_after_update[user] = tk.get_action("user_show")(
                get_context(), {"id": user, "include_password_hash": True}
            )["password_hash"]

        assert_equal(
            initial_user_passwords[self.site_user],
            user_passwords_after_update[self.site_user],
            "The user at position 0 in the list should not have been updated",
        )
        assert_not_equal(
            initial_user_passwords["user0"],
            user_passwords_after_update["user0"],
            "The user at position 1 in the list should have been updated",
        )
        assert_not_equal(
            initial_user_passwords["user1"],
            user_passwords_after_update["user1"],
            "The user at position 2 in the list should have been updated",
        )
        assert_equal(
            initial_user_passwords["user2"],
            user_passwords_after_update["user2"],
            "The user at position 3 in the list should not have been updated",
        )

    def test_own_password_is_not_reset_single_user_password(self):
        context = get_context()
        context["ignore_auth"] = False

        result = tk.get_action("ogdch_force_reset_passwords")(
            context, {"user": self.site_user}
        )

        assert_equal(
            [],
            result["success_users"],
            "Should not reset password for the user we are using to call the action",
        )
        assert_equal(
            f"Not resetting password for the signed-in user {self.site_user}",
            result["errors"][self.site_user],
            "Expected error when resetting password for the user we are using to call the action",
        )

    def test_own_password_is_not_reset_multiple_user_passwords(self):
        context = get_context()
        context["ignore_auth"] = False
        # We have four users: [u'default', u'user0', u'user1', u'user2']
        result = tk.get_action("ogdch_force_reset_passwords")(
            context, {"limit": "2", "offset": "0"}
        )

        assert_equal(
            ["user0"],
            result["success_users"],
            "Password should have been reset for the user we are not using to call the action",
        )
        assert_equal(
            f"Not resetting password for the signed-in user {self.site_user}",
            result["errors"][self.site_user],
            "Expected error when resetting password for the user we are using to call the action",
        )

    def check_email(self, email, address, name, subject):
        assert_equal(email[1], "ckan@localhost")
        assert_equal(email[2], [address])
        assert_in(name, email[3])
        encoded_subject = (
            f"Subject: =?utf-8?q?{subject.replace(' ', '_').replace('.', '=2E')}"
        )
        assert_in(encoded_subject, email[3])

    def test_sending_reset_link_default(self):
        context = get_context()
        context["ignore_auth"] = False
        tk.get_action("ogdch_force_reset_passwords")(context, {"user": "user0"})

        email = self.get_smtp_messages()[0]
        self.check_email(
            email, "user0@example.org", "user0", "Reset your password - opendata.swiss"
        )
        self.clear_smtp_messages()

    def test_sending_reset_link_notify_true(self):
        context = get_context()
        context["ignore_auth"] = False
        tk.get_action("ogdch_force_reset_passwords")(
            context, {"user": "user0", "notify": True}
        )

        email = self.get_smtp_messages()[0]
        self.check_email(
            email, "user0@example.org", "user0", "Reset your password - opendata.swiss"
        )
        self.clear_smtp_messages()

    def test_sending_reset_link_notify_false(self):
        context = get_context()
        context["ignore_auth"] = False
        tk.get_action("ogdch_force_reset_passwords")(
            context, {"user": "user0", "notify": False}
        )

        assert_equal(len(self.get_smtp_messages()), 0)
        self.clear_smtp_messages()
