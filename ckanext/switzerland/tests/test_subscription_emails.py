import datetime
from unittest.mock import patch

import ckan.tests.factories as ckan_factories
import pytest
from ckan import model
from ckan import plugins as p
from ckan.lib.helpers import url_for
from ckan.tests import helpers

from ckanext.subscribe import model as subscribe_model
from ckanext.subscribe.email_verification import (
    get_verification_email_vars,
)
from ckanext.subscribe.notification import dictize_notifications
from ckanext.subscribe.notification_email import get_notification_email_vars
from ckanext.subscribe.tests import factories
from ckanext.switzerland.plugins import OgdchSubscribePlugin
from ckanext.switzerland.tests.conftest import get_context

config = p.toolkit.config


def _test_all_four_languages(body, object_title_included=False):
    if object_title_included:
        assert "Geschäftsstelle Open Government Data" in body
        assert "Open Government Data Office" in body
        assert "Secrétariat Open Government Data" in body
        assert "Segreteria Open Government Data" in body

    # Check that there is a sign-off in each language
    assert "Team Geschäftsstelle OGD" in body
    assert "The OGD office team" in body
    assert "L'équipe du secrétariat OGD" in body
    assert "Team Segreteria OGD" in body


def _test_plain_text_footer(body_plain_text, dataset_id, subscription=False, code=""):
    assert (
        """Geschäftsstelle Open Government Data
Bundesamt für Statistik BFS
Espace de l'Europe 10
CH-2010 Neuchâtel
www.bfs.admin.ch/ogd
"""
        in body_plain_text
    )

    footer_link_text = ""
    if subscription:
        footer_link_text = (
            f"Abonnement löschen: http://frontend-test.ckan.net/"
            f"subscribe/unsubscribe?code=testcode&amp;dataset={dataset_id}\n"
        )
    if code:
        footer_link_text += (
            f"Mein Abonnement verwalten: http://frontend-test.ckan.net/"
            f"subscribe/manage?code={code}"
        )

    assert footer_link_text in body_plain_text


def _test_html_footer(body_html, dataset_id, subscription=False, code=""):
    assert (
        """<p>
    <a href="https://opendata.swiss">
        <img src="https://opendata.swiss/images/logo_horizontal.png" alt="opendata.swiss"
             width="420" style="max-width: 100%; height: auto;"/>
    </a>
</p>
<p>
    <a href="https://twitter.com/opendataswiss">
        <img src="https://opendata.swiss/images/x.svg" alt="X"
             style="color: #fff; background-color: #009688; border: 0;"/>
    </a>
</p>"""
        in body_html
    )

    footer_link_text = ""
    if subscription:
        footer_link_text = (
            f'<a href="http://frontend-test.ckan.net/'
            f'subscribe/unsubscribe?code=testcode&amp;dataset={dataset_id}">'
            f"Abonnement löschen</a> | "
        )
    if code:
        footer_link_text += (
            f'<a href="http://frontend-test.ckan.net/'
            f'subscribe/manage?code={code}">Mein Abonnement verwalten</a>'
        )

    assert footer_link_text in body_html


def trigger_notifications(app, sysadmin_headers):
    url = url_for(
        "api.action",
        logic_function="subscribe_send_any_notifications",
        ver=3,
    )
    app.post(
        url,
        headers=sysadmin_headers,
    )


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch ogdch_pkg ogdch_org ogdch_showcase ogdch_subscribe ogdch_dcat scheming_datasets fluent activity",
)
@pytest.mark.ckan_config("ckan.site_url", "http://test.ckan.net")
@pytest.mark.ckan_config(
    "ckanext.switzerland.frontend_url", "http://frontend-test.ckan.net"
)
@pytest.mark.ckan_config("ckanext.subscribe.apply_recaptcha", False)
@pytest.mark.usefixtures(
    "with_plugins", "clean_db_and_migrate_for_ogdch_subscribe", "clean_index"
)
class TestSubscriptionEmails(object):
    def test_get_email_vars_with_subscription(self, app, dataset):
        subscription = factories.Subscription(
            dataset_id=dataset["id"], return_object=True
        )

        subscribe = OgdchSubscribePlugin()
        email_vars = subscribe.get_email_vars(
            code="testcode", subscription=subscription, email=None
        )

        assert email_vars["site_title"] == config["ckan.site_title"]
        assert email_vars["object_title_de"] == "DE Test"
        assert email_vars["object_title_en"] == "EN Test"
        assert email_vars["object_title_fr"] == "FR Test"
        assert email_vars["object_title_it"] == "IT Test"
        assert email_vars["object_type"] == "dataset"
        assert email_vars["email"] == "bob@example.com"

        assert (
            email_vars["manage_link"]
            == "http://frontend-test.ckan.net/subscribe/manage?code=testcode"
        )
        assert (
            email_vars["object_link"]
            == f"http://frontend-test.ckan.net/dataset/{dataset['id']}"
        )
        assert (
            email_vars["unsubscribe_all_link"]
            == "http://frontend-test.ckan.net/subscribe/unsubscribe-all?code=testcode"
        )
        assert (
            email_vars["unsubscribe_link"] == f"http://frontend-test.ckan.net/"
            f"subscribe/unsubscribe?code=testcode&dataset={dataset['id']}"
        )

    def test_get_email_vars_with_email(self, app, dataset):
        subscribe = OgdchSubscribePlugin()
        email_vars = subscribe.get_email_vars(
            code="testcode", subscription=None, email="bob@example.com"
        )

        assert email_vars["site_title"] == config["ckan.site_title"]
        assert email_vars["email"] == "bob@example.com"
        assert (
            email_vars["manage_link"]
            == "http://frontend-test.ckan.net/subscribe/manage?code=testcode"
        )
        assert (
            email_vars["unsubscribe_all_link"]
            == "http://frontend-test.ckan.net/subscribe/unsubscribe-all?code=testcode"
        )

        assert "object_type" not in email_vars
        assert "object_title" not in email_vars
        assert "object_name" not in email_vars
        assert "object_link" not in email_vars
        assert "unsubscribe_link" not in email_vars

    # Horrible unittest.mock gotcha: these patch decorators have to be listed in the
    # *opposite* order from the variables in the test-function signature.
    @patch("ckanext.subscribe.mailer.mail_recipient")
    @patch("ckanext.subscribe.email_auth.create_code")
    def test_get_verification_email_contents(
        self,
        mock_create_code,
        mock_mail_recipient,
        app,
        dataset,
    ):
        mock_create_code.return_value = "testcode"

        url = url_for("subscribe.signup")
        app.post(url, data={"email": "bob@example.com", "dataset": dataset["id"]})

        mock_mail_recipient.assert_called_once()

        # Email subject
        subject = mock_mail_recipient.call_args[1]["subject"]
        assert (
            subject
            == "Best\xe4tigungsmail – Confirmation - E-mail di conferma - Confirmation"
        )

        # Email plain-text body
        body_plain_text = mock_mail_recipient.call_args[1]["body"]
        assert (
            """Vielen Dank, dass Sie sich für den Datensatz"""
            in body_plain_text.strip()
        )
        assert "http://test.ckan.net" not in body_plain_text
        _test_plain_text_footer(
            body_plain_text, dataset["id"], subscription=False, code=""
        )
        _test_all_four_languages(body_plain_text, object_title_included=True)

        # Email HTML body
        body_html = mock_mail_recipient.call_args[1]["body_html"]
        assert (
            """Vielen Dank, dass Sie sich f\xfcr den Datensatz""" in body_html.strip()
        )
        assert "http://test.ckan.net" not in body_html

        _test_html_footer(body_html, dataset["id"], subscription=False, code="")
        _test_all_four_languages(body_html, object_title_included=True)

    @patch("ckanext.subscribe.mailer.mail_recipient")
    @patch("ckanext.subscribe.email_auth.create_code")
    def test_get_manage_email_contents(
        self,
        mock_create_code,
        mock_mail_recipient,
        app,
        dataset,
    ):
        mock_create_code.return_value = "testcode"
        subscription = factories.Subscription(
            dataset_id=dataset["id"], return_object=True
        )

        url = url_for("subscribe.request_manage_code")
        app.get(url, data={"email": "bob@example.com"})

        mock_mail_recipient.assert_called_once()

        # Email subject
        subject = mock_mail_recipient.call_args[1]["subject"]
        assert subject == "Manage opendata.swiss subscription"

        # Email plain-text body
        body_plain_text = mock_mail_recipient.call_args[1]["body"]
        assert """To manage subscriptions for""" in body_plain_text.strip()
        assert "http://test.ckan.net" not in body_plain_text
        _test_plain_text_footer(
            body_plain_text,
            dataset["id"],
            subscription=False,
            code=subscription.verification_code,
        )
        _test_all_four_languages(body_plain_text, object_title_included=False)

        # Email HTML body
        body_html = mock_mail_recipient.call_args[1]["body_html"]
        assert (
            """<p>
    To manage subscriptions for"""
            in body_html.strip()
        )
        assert "http://test.ckan.net" not in body_html

        _test_html_footer(
            body_html,
            dataset["id"],
            subscription=False,
            code=subscription.verification_code,
        )
        _test_all_four_languages(body_html, object_title_included=False)

    @patch("ckanext.subscribe.mailer.mail_recipient")
    @patch("ckanext.subscribe.email_auth.create_code")
    def test_get_subscription_confirmation_email_contents(
        self,
        mock_create_code,
        mock_mail_recipient,
        app,
        dataset,
    ):
        mock_create_code.return_value = "testcode"
        factories.SubscriptionLowLevel(
            object_id=dataset["id"],
            object_type="dataset",
            email="bob@example.com",
            frequency=subscribe_model.Frequency.IMMEDIATE.value,
            verification_code="testcode",
            verification_code_expires=datetime.datetime.now()
            + datetime.timedelta(hours=1),
        )

        url = url_for("subscribe.verify_subscription")
        app.get(url, params={"code": "testcode"})

        mock_mail_recipient.assert_called_once()

        # Email subject
        subject = mock_mail_recipient.call_args[1]["subject"]
        assert (
            subject
            == "Best\xe4tigungsmail – Confirmation - E-mail di conferma - Confirmation"
        )

        # Email plain-text body
        body_plain_text = mock_mail_recipient.call_args[1]["body"]
        assert (
            """Sie haben Ihre E-Mail-Adresse erfolgreich bestätigt."""
            in body_plain_text.strip()
        )
        assert "http://test.ckan.net" not in body_plain_text
        _test_plain_text_footer(
            body_plain_text, dataset["id"], subscription=True, code="testcode"
        )
        _test_all_four_languages(body_plain_text, object_title_included=False)

        # Email HTML body
        body_html = mock_mail_recipient.call_args[1]["body_html"]
        assert (
            """<p>
    Sie haben Ihre E-Mail-Adresse erfolgreich bestätigt. """
            in body_html.strip()
        )
        assert "http://test.ckan.net" not in body_html

        _test_html_footer(body_html, dataset["id"], subscription=True, code="testcode")
        _test_all_four_languages(body_html, object_title_included=False)

    @patch("ckanext.switzerland.helpers.backend_helpers.get_contact_point_for_dataset")
    @patch("ckanext.subscribe.mailer.mail_recipient")
    @patch("ckanext.subscribe.email_auth.create_code")
    def test_get_notification_email_contents(
        self,
        mock_create_code,
        mock_mail_recipient,
        mock_get_contact_point,
        app,
        dataset,
        sysadmin_headers,
        no_notification_users,
    ):
        mock_create_code.return_value = "testcode"
        mock_get_contact_point.return_value = [
            {"name": "Open-Data-Plattform", "email": "contact@odp.ch"}
        ]

        # Change our dataset to generate a "changed package" activity
        p.toolkit.get_action("package_patch")(
            get_context(), {"id": dataset["id"], "url": "http://new_url"}
        )
        # Create a subscription to our dataset that will get a notification email
        factories.Subscription(dataset_id=dataset["id"], return_object=True)

        trigger_notifications(app, sysadmin_headers)

        mock_mail_recipient.assert_called_once()

        # Email subject
        subject = mock_mail_recipient.call_args[1]["subject"]
        assert subject == "Update notification – updated dataset opendata.swiss"

        # Email plain-text body
        body_plain_text = mock_mail_recipient.call_args[1]["body"]
        assert (
            "Es gibt eine \xc4nderung im Datensatz DE Test. Um die \xc4nderung zu sehen, klicken Sie bitte"
            in body_plain_text.strip()
        )
        assert (
            f"http://frontend-test.ckan.net/dataset/{dataset['id']}"
            in body_plain_text.strip()
        )
        assert "http://test.ckan.net" not in body_plain_text
        _test_plain_text_footer(
            body_plain_text, dataset["id"], subscription=False, code="testcode"
        )
        _test_all_four_languages(body_plain_text, object_title_included=True)

        # Email HTML body
        body_html = mock_mail_recipient.call_args[1]["body_html"]
        assert (
            "Es gibt eine \xc4nderung im Datensatz DE Test. Um die \xc4nderung zu sehen, klicken Sie bitte"
            in body_html.strip()
        )
        assert (
            '<a href="http://frontend-test.ckan.net/dataset/{dataset_id}">'
            "http://frontend-test.ckan.net/dataset/{dataset_id}</a>".format(
                dataset_id=dataset["id"]
            )
            in body_html.strip()
        )
        assert "http://test.ckan.net" not in body_html
        _test_html_footer(body_html, dataset["id"], subscription=False, code="testcode")
        _test_all_four_languages(body_html, object_title_included=True)

    @patch("ckanext.switzerland.helpers.backend_helpers.get_contact_point_for_dataset")
    @patch("ckanext.subscribe.mailer.mail_recipient")
    @patch("ckanext.subscribe.email_auth.create_code")
    def test_get_deletion_email_contents(
        self,
        mock_create_code,
        mock_mail_recipient,
        mock_get_contact_point,
        app,
        dataset,
        sysadmin_headers,
        no_notification_users,
    ):
        mock_create_code.return_value = "testcode"
        contact_points = [{"name": "Open-Data-Plattform", "email": "contact@odp.ch"}]
        mock_get_contact_point.return_value = contact_points

        # Delete our dataset to generate a "deleted package" activity
        p.toolkit.get_action("package_delete")(get_context(), {"id": dataset["id"]})
        # Create a subscription to our dataset that will get a notification email
        factories.Subscription(dataset_id=dataset["id"], return_object=True)

        trigger_notifications(app, sysadmin_headers)

        # Two emails are sent here, not just one, so we can't do
        # mock_mail_recipient.assert_called_once().
        # There is one email for the package being created, and one for it being
        # deleted. This is an artefact of how factories.Subscription works: it
        # backdates the subscription's creation date to one hour ago, so both the
        # 'new package' and 'deleted package' activities are notified about.
        # In test_get_notification_email_contents above, there is only *one* email sent,
        # because ckanext-subscribe bundles the 'new package' and 'changed package'
        # notifications, but it does not bundle the 'deleted package' notification.
        # TODO: This should be tidied up in ckanext-subscribe. Then this test will need
        # to be adjusted.
        mock_mail_recipient.assert_called()

        # Email subject
        mail_recipient_args = mock_mail_recipient.call_args_list[1][1]
        subject = mail_recipient_args["subject"]
        assert subject == "Delete notification – deleted dataset opendata.swiss"

        # Email plain-text body
        body_plain_text = mail_recipient_args["body"]
        assert (
            'Hello,\nWe inform you that the dataset "EN Test" you subscribed to has '
            "been removed from our portal by the data provider."
            in body_plain_text.strip()
        )
        assert contact_points[0].get("name") in body_plain_text.strip()
        assert contact_points[0].get("email") in body_plain_text.strip()
        assert "http://test.ckan.net" not in body_plain_text

        # Email HTML body
        body_html = mail_recipient_args["body_html"]
        assert (
            '<p>Hello,</p>\n\n<p>We inform you that the dataset "<b>EN Test</b>" you '
            "subscribed to has been removed from our portal" in body_html.strip()
        )
        assert (
            f"<a href=\"mailto:{contact_points[0].get('email')}\">"
            f"{contact_points[0].get('name')}</a>" in body_html.strip()
        )
        assert "http://test.ckan.net" not in body_html

    def test_get_activities(self, app, dataset):
        """Test that we don't get activities from the migration and harvest users."""
        normal_activity = factories.Activity(
            object_id=dataset["id"],
            activity_type="changed package",
            return_object=True,
        )
        migration = ckan_factories.User(name="migration", sysadmin=True)
        factories.Activity(
            user=migration,
            user_id=migration["id"],
            object_id=dataset["id"],
            activity_type="changed package",
        )
        harvest = ckan_factories.User(name="harvest", sysadmin=True)
        factories.Activity(
            user=harvest,
            user_id=harvest["id"],
            object_id=dataset["id"],
            activity_type="changed package",
        )

        now = datetime.datetime.now()
        day = datetime.timedelta(days=1)
        include_activity_from = now - day

        subscribe = OgdchSubscribePlugin()
        activities = subscribe.get_activities(
            include_activity_from=include_activity_from,
            objects_subscribed_to_keys=[dataset["id"]],
        )

        # One 'new package' activity, and one 'changed package' activity
        assert len(activities) == 2
        assert activities[0].activity_type == "new package"
        assert activities[1].user_id == normal_activity.user_id
        assert activities[1].activity_type == "changed package"
