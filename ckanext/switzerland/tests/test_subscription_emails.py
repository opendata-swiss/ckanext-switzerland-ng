import datetime

import ckan.tests.factories as ckan_factories
import pytest
from ckan import plugins as p
from mock import patch

from ckanext.subscribe.email_verification import (
    get_verification_email_vars,
)
from ckanext.subscribe.notification_email import get_notification_email_vars
from ckanext.subscribe.tests import factories
from ckanext.switzerland.plugins import OgdchSubscribePlugin

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


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch ogdch_pkg ogdch_subscribe scheming_datasets fluent activity",
)
@pytest.mark.usefixtures(
    "with_plugins", "clean_db_and_migrate_for_ogdch_subscribe", "clean_index"
)
class TestSubscriptionEmails(object):
    def test_get_email_vars_with_subscription(self, dataset):
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

    def test_get_email_vars_with_email(self, dataset):
        subscribe = OgdchSubscribePlugin()
        email_vars = subscribe.get_email_vars(
            code="testcode", subscription=None, email="bob@example.com"
        )

        assert email_vars["site_title"] == config["ckan.site_title"]
        assert email_vars["site_url"] == "http://test.ckan.net"

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

    def test_get_verification_email_contents(self, dataset):
        subscription = factories.Subscription(
            dataset_id=dataset["id"], return_object=True
        )
        subscription.verification_code = "testcode"

        subscribe = OgdchSubscribePlugin()
        email_vars = get_verification_email_vars(subscription)
        subject, body_plain_text, body_html = subscribe.get_verification_email_contents(
            email_vars
        )

        assert (
            subject
            == "Best\xe4tigungsmail \\u2013 Confirmation - E-mail di conferma - Confirmation"
        )
        assert (
            """Vielen Dank, dass Sie sich für den Datensatz"""
            in body_plain_text.strip()
        )
        assert (
            """Vielen Dank, dass Sie sich f\xfcr den Datensatz""" in body_html.strip()
        )
        assert "http://test.ckan.net" not in body_html
        assert "http://test.ckan.net" not in body_plain_text

        _test_html_footer(body_html, dataset["id"], subscription=False, code="")
        _test_plain_text_footer(
            body_plain_text, dataset["id"], subscription=False, code=""
        )
        _test_all_four_languages(body_html, object_title_included=True)
        _test_all_four_languages(body_plain_text, object_title_included=True)

    def test_get_manage_email_contents(self, dataset):
        subscription = factories.Subscription(
            dataset_id=dataset["id"], return_object=True
        )
        subscription.verification_code = "testcode"

        subscribe = OgdchSubscribePlugin()
        email_vars = subscribe.get_email_vars(
            code=subscription.verification_code, subscription=subscription
        )
        subject, body_plain_text, body_html = subscribe.get_manage_email_contents(
            email_vars
        )

        assert subject == "Manage opendata.swiss subscription"
        assert """To manage subscriptions for""" in body_plain_text.strip()
        assert (
            """<p>
    To manage subscriptions for"""
            in body_html.strip()
        )
        assert "http://test.ckan.net" not in body_html
        assert "http://test.ckan.net" not in body_plain_text

        _test_html_footer(
            body_html,
            dataset["id"],
            subscription=False,
            code=subscription.verification_code,
        )
        _test_plain_text_footer(
            body_plain_text,
            dataset["id"],
            subscription=False,
            code=subscription.verification_code,
        )
        _test_all_four_languages(body_html, object_title_included=False)
        _test_all_four_languages(body_plain_text, object_title_included=False)

    def test_get_subscription_confirmation_email_contents(self, dataset):
        subscription = factories.Subscription(
            dataset_id=dataset["id"], return_object=True
        )
        code = "testcode"

        subscribe = OgdchSubscribePlugin()
        email_vars = subscribe.get_email_vars(code=code, subscription=subscription)
        subject, body_plain_text, body_html = (
            subscribe.get_subscription_confirmation_email_contents(email_vars)
        )

        assert (
            subject
            == "Best\xe4tigungsmail \\u2013 Confirmation - E-mail di conferma - Confirmation"
        )
        assert (
            """Sie haben Ihre E-Mail-Adresse erfolgreich bestätigt."""
            in body_plain_text.strip()
        )
        assert (
            """<p>
    Sie haben Ihre E-Mail-Adresse erfolgreich bestätigt. """
            in body_html.strip()
        )
        assert "http://test.ckan.net" not in body_html
        assert "http://test.ckan.net" not in body_plain_text

        _test_html_footer(body_html, dataset["id"], subscription=True, code=code)
        _test_plain_text_footer(
            body_plain_text, dataset["id"], subscription=True, code=code
        )
        _test_all_four_languages(body_html, object_title_included=False)
        _test_all_four_languages(body_plain_text, object_title_included=False)

    @patch("ckanext.switzerland.helpers.backend_helpers.get_contact_point_for_dataset")
    def test_get_notification_email_contents(self, dataset, mock_get_contact_point):
        mock_get_contact_point.return_value = [
            {"name": "Open-Data-Plattform", "email": "contact@odp.ch"}
        ]
        code = "testcode"
        email = "bob@example.com"
        subscription = factories.Subscription(
            dataset_id=dataset["id"], return_object=False
        )
        notifications = [
            {
                "subscription": subscription,
                "activities": [
                    {
                        "user_id": "admin",
                        "object_id": "test-object-id",
                        "revision_id": "test-revision-id-1",
                        "activity_type": "changed package",
                        "timestamp": "2022-10-12T12:00:00",
                        "data": {
                            "package": {
                                "name": "test-dataset",
                                "title": '{"fr": "FR Test", "de": "DE Test", "en": "EN Test", "it": "IT Test"}',
                            }
                        },
                    }
                ],
            }
        ]

        email_vars = get_notification_email_vars(
            code=code, email=email, notifications=notifications
        )
        subscribe = OgdchSubscribePlugin()
        subject, body_plain_text, body_html = subscribe.get_notification_email_contents(
            email_vars
        )

        assert subject == "Update notification \\u2013 updated dataset opendata.swiss"
        assert (
            "Es gibt eine \xc4nderung im Datensatz DE Test. Um die \xc4nderung zu sehen, klicken Sie bitte"
            in body_plain_text.strip()
        )
        assert (
            "Es gibt eine \xc4nderung im Datensatz DE Test. Um die \xc4nderung zu sehen, klicken Sie bitte"
            in body_html.strip()
        )
        assert (
            f"http://frontend-test.ckan.net/dataset/{dataset['id']}"
            in body_plain_text.strip()
        )
        assert (
            '<a href="http://frontend-test.ckan.net/dataset/{dataset_id}">'
            "http://frontend-test.ckan.net/dataset/{dataset_id}</a>".format(
                dataset_id=dataset["id"]
            )
            in body_html.strip()
        )

        assert "http://test.ckan.net" not in body_html
        assert "http://test.ckan.net" not in body_plain_text

        _test_html_footer(body_html, dataset["id"], subscription=False, code=code)
        _test_plain_text_footer(
            body_plain_text, dataset["id"], subscription=False, code=code
        )
        _test_all_four_languages(body_html, object_title_included=True)
        _test_all_four_languages(body_plain_text, object_title_included=True)

    @patch("ckanext.switzerland.helpers.backend_helpers.get_contact_point_for_dataset")
    def test_get_deletion_email_contents(self, dataset, mock_get_contact_point):
        contact_points = [{"name": "Open-Data-Plattform", "email": "contact@odp.ch"}]
        mock_get_contact_point.return_value = contact_points
        code = "testcode"
        email = "bob@example.com"
        subscription = factories.Subscription(
            dataset_id=dataset["id"], return_object=False
        )
        notifications = [
            {
                "subscription": subscription,
                "activities": [
                    {
                        "user_id": "admin",
                        "object_id": "test-object-id",
                        "revision_id": "test-revision-id-1",
                        "activity_type": "deleted package",
                        "timestamp": "2022-10-12T12:00:00",
                        "data": {
                            "package": {
                                "name": "test-dataset",
                                "title": '{"fr": "FR Test", "de": "DE Test", "en": "EN Test", "it": "IT Test"}',
                            }
                        },
                    }
                ],
            }
        ]

        email_vars = get_notification_email_vars(
            code=code, email=email, notifications=notifications
        )
        subscribe = OgdchSubscribePlugin()
        subject, body_plain_text, body_html = subscribe.get_notification_email_contents(
            email_vars, type="deletion"
        )

        assert subject == "Delete notification \\u2013 deleted dataset opendata.swiss"
        assert (
            'Hello,\nWe inform you that the dataset "EN Test" you subscribed to has '
            "been removed from our portal by the data provider."
            in body_plain_text.strip()
        )
        assert (
            '<p>Hello,</p>\n\n<p>We inform you that the dataset "<b>EN Test</b>" you '
            "subscribed to has been removed from our portal" in body_html.strip()
        )
        assert contact_points[0].get("name") in body_plain_text.strip()
        assert contact_points[0].get("email") in body_plain_text.strip()
        assert (
            f"<a href=\"mailto:{contact_points[0].get('email')}\">"
            f"{contact_points[0].get('name')}</a>" in body_html.strip()
        )

        assert "http://test.ckan.net" not in body_html
        assert "http://test.ckan.net" not in body_plain_text

    def test_get_activities(self, dataset):
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
