import logging

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import pytest
from ckan.lib.helpers import url_for
from ckan.plugins.toolkit import config

from ckanext.switzerland.tests.conftest import get_context

log = logging.getLogger(__name__)


def check_email(email, address, name, subject):
    assert email[1] == "ckan@localhost"
    assert email[2] == [address]
    assert name in email[3]
    assert subject in email[3]


def force_reset_passwords(app, user, data_dict):
    url = url_for(
        "api.action",
        logic_function="ogdch_force_reset_passwords",
        ver=3,
    )
    resp = app.post(
        url,
        headers={"Authorization": user["token"]},
        data=data_dict,
    )
    return resp.json["result"]


@pytest.mark.ckan_config("ckan.plugins", "ogdch password_policy")
@pytest.mark.ckan_config("smtp.mail_from", "ckan@localhost")
@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestForceResetPasswords(object):
    def test_reset_single_user_password(self, app, site_user, users):
        initial_user = tk.get_action("user_show")(
            get_context(), {"id": "user0", "include_password_hash": True}
        )

        initial_other_user_passwords = {}
        for user in ["user1", "user2", site_user]:
            initial_other_user_passwords[user] = tk.get_action("user_show")(
                get_context(), {"id": user, "include_password_hash": True}
            )["password_hash"]

        sysadmin_user = factories.SysadminWithToken()
        result = force_reset_passwords(
            app, sysadmin_user, data_dict={"user": "user0", "notify": False}
        )

        updated_user = tk.get_action("user_show")(
            get_context(), {"id": "user1", "include_password_hash": True}
        )
        other_user_passwords_after_reset = {}
        for user in ["user1", "user2", site_user]:
            other_user_passwords_after_reset[user] = tk.get_action("user_show")(
                get_context(), {"id": user, "include_password_hash": True}
            )["password_hash"]

        assert ["user0"] == result["success_users"]
        assert {} == result["errors"]
        assert updated_user["password_hash"] != initial_user["password_hash"]
        assert initial_other_user_passwords == other_user_passwords_after_reset

    def test_reset_multiple_user_passwords(self, app, users):
        sysadmin_user = factories.SysadminWithToken()
        sysadmin_name = sysadmin_user["name"]
        users.append(sysadmin_name)
        initial_user_passwords = {}

        # We have four users in total: ["user0", "user1", "user2", sysadmin_name]
        for user in users:
            initial_user_passwords[user] = tk.get_action("user_show")(
                get_context(), {"id": user, "include_password_hash": True}
            )["password_hash"]

        force_reset_passwords(
            app, sysadmin_user, data_dict={"limit": "2", "offset": "1"}
        )

        user_passwords_after_update = {}
        for user in users:
            user_passwords_after_update[user] = tk.get_action("user_show")(
                get_context(), {"id": user, "include_password_hash": True}
            )["password_hash"]

        assert initial_user_passwords["user0"] != user_passwords_after_update["user0"]
        assert initial_user_passwords["user1"] != user_passwords_after_update["user1"]
        assert initial_user_passwords["user2"] == user_passwords_after_update["user2"]
        assert (
            initial_user_passwords[sysadmin_name]
            == user_passwords_after_update[sysadmin_name]
        )

    def test_own_password_is_not_reset_single_user_password(self, app):
        sysadmin_user = factories.SysadminWithToken()
        sysadmin_name = sysadmin_user["name"]

        result = force_reset_passwords(
            app, sysadmin_user, data_dict={"user": sysadmin_name}
        )

        assert [] == result["success_users"]
        assert (
            f"Not resetting password for the signed-in user {sysadmin_name}"
            == result["errors"][sysadmin_name]
        )

    def test_own_password_is_not_reset_multiple_user_passwords(
        self, app, users, mail_server
    ):
        # The list of users we act upon when resetting multiple user's passwords is
        # sorted by display_name. Set the sysadmin's fullname (used as their
        # display_name), so we know they will be sorted after the three regular users.
        sysadmin_user = factories.SysadminWithToken(fullname="xxx_sysadmin_xxx")
        sysadmin_name = sysadmin_user["name"]
        users.append(sysadmin_name)

        # We have four users in total: ["user0", "user1", "user2", "xxx_sysadmin_xxx"]
        result = force_reset_passwords(
            app, sysadmin_user, data_dict={"limit": "2", "offset": "2"}
        )

        assert ["user2"] == result["success_users"]
        assert (
            f"Not resetting password for the signed-in user {sysadmin_name}"
            == result["errors"][sysadmin_name]
        )

    def test_sending_reset_link_default(self, app, users, mail_server):
        sysadmin_user = factories.SysadminWithToken()
        force_reset_passwords(app, sysadmin_user, data_dict={"user": "user0"})

        email = mail_server.get_smtp_messages()[0]
        check_email(
            email, "user0@example.org", "user0", "Reset your password - opendata.swiss"
        )

    def test_sending_reset_link_notify_true(self, app, users, mail_server):
        sysadmin_user = factories.SysadminWithToken()
        force_reset_passwords(
            app, sysadmin_user, data_dict={"user": "user0", "notify": True}
        )

        email = mail_server.get_smtp_messages()[0]
        check_email(
            email, "user0@example.org", "user0", "Reset your password - opendata.swiss"
        )

    def test_sending_reset_link_notify_false(self, app, users, mail_server):
        sysadmin_user = factories.SysadminWithToken()
        force_reset_passwords(
            app, sysadmin_user, data_dict={"user": "user0", "notify": False}
        )

        assert len(mail_server.get_smtp_messages()) == 0
