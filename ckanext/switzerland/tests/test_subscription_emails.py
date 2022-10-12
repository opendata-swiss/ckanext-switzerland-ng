# encoding: utf-8

from nose.tools import assert_equal, assert_in, assert_not_in

import ckan.plugins.toolkit as tk
import ckan.model as model

from ckan import plugins as p
from ckan.tests import helpers

from ckanext.subscribe import model as subscribe_model
from ckanext.subscribe.email_verification import (
    get_verification_email_vars,
)
from ckanext.subscribe.notification_email import (
    get_notification_email_vars
)
from ckanext.subscribe.tests import factories
from ckanext.switzerland.plugins import OgdchSubscribePlugin

config = p.toolkit.config


class TestSubscriptionEmails(helpers.FunctionalTestBase):

    @classmethod
    def teardown_class(cls):
        super(TestSubscriptionEmails, cls).teardown_class()
        helpers.reset_db()

    def setup(self):
        super(TestSubscriptionEmails, self).setup()
        subscribe_model.setup()
        user = tk.get_action('get_site_user')({'ignore_auth': True})['name']
        context = {'model': model, 'session': model.Session,
                   'user': user, 'ignore_auth': True}
        # create an org
        self.org = {
            'name': 'test-org',
            'title': {
                'de': 'Test Org DE',
                'fr': 'Test Org FR',
                'it': 'Test Org IT',
                'en': 'Test Org EN',
            },
            'political_level': 'confederation'
        }
        tk.get_action('organization_create')(context, self.org)

        # create a valid DCAT-AP Switzerland compliant dataset
        self.dataset_dict = {
            'coverage': '',
            'issued': '08.09.2015',
            'contact_points': [{'email': 'pierre@bar.ch', 'name': 'Pierre'}],
            'keywords': {
                'fr': [],
                'de': [],
                'en': [],
                'it': []
            },
            'spatial': '',
            'publisher': {'name': 'Bundesarchiv', 'url':'https//opendata.swiss/organization/bundesarchiv'},
            'description': {
                'fr': 'Description FR',
                'de': 'Beschreibung DE',
                'en': 'Description EN',
                'it': 'Description IT'
            },
            'title': {
                'fr': 'FR Test',
                'de': 'DE Test',
                'en': 'EN Test',
                'it': 'IT Test'
            },
            'language': [
                'en',
                'de'
            ],
            'name': 'test-dataset',
            'relations': [],
            'see_alsos': [],
            'temporals': [],
            'accrual_periodicity': 'http://publications.europa.eu/resource/authority/frequency/IRREG',
            'modified': '09.09.2015',
            'url': 'http://some_url',
            'owner_org': 'test-org',
            'identifier': 'test1@test-org'
        }
        self.dataset = tk.get_action('package_create')(context, self.dataset_dict)

    def test_get_email_vars_with_subscription(self):
        subscription = factories.Subscription(
            dataset_id=self.dataset['id'], return_object=True)

        subscribe = OgdchSubscribePlugin()
        email_vars = subscribe.get_email_vars(
            code='testcode',
            subscription=subscription,
            email=None
        )

        assert_equal(email_vars['site_title'], config['ckan.site_title'])
        assert_equal(email_vars['object_title_de'], 'DE Test')
        assert_equal(email_vars['object_title_en'], 'EN Test')
        assert_equal(email_vars['object_title_fr'], 'FR Test')
        assert_equal(email_vars['object_title_it'], 'IT Test')
        assert_equal(email_vars['object_type'], 'dataset')
        assert_equal(email_vars['email'], 'bob@example.com')

        assert_equal(email_vars['manage_link'],
                     'http://frontend-test.ckan.net/subscribe/manage?code=testcode')
        assert_equal(email_vars['object_link'],
                     'http://frontend-test.ckan.net/dataset/{}'.format(self.dataset['id']))
        assert_equal(email_vars['unsubscribe_all_link'],
                     'http://frontend-test.ckan.net/subscribe/unsubscribe-all?code=testcode')
        assert_equal(email_vars['unsubscribe_link'],
                     'http://frontend-test.ckan.net/subscribe/unsubscribe?code=testcode&dataset={}'
                     .format(self.dataset['id']))

    def test_get_email_vars_with_email(self):
        subscribe = OgdchSubscribePlugin()
        email_vars = subscribe.get_email_vars(
            code='testcode',
            subscription=None,
            email='bob@example.com'
        )

        assert_equal(email_vars['site_title'], config['ckan.site_title'])
        assert_equal(email_vars['site_url'], 'http://test.ckan.net')

        assert_equal(email_vars['email'], 'bob@example.com')
        assert_equal(email_vars['manage_link'],
                     'http://frontend-test.ckan.net/subscribe/manage?code=testcode')
        assert_equal(email_vars['unsubscribe_all_link'],
                     'http://frontend-test.ckan.net/subscribe/unsubscribe-all?code=testcode')

        assert_not_in('object_type', email_vars)
        assert_not_in('object_title', email_vars)
        assert_not_in('object_name', email_vars)
        assert_not_in('object_link', email_vars)
        assert_not_in('unsubscribe_link', email_vars)

    def test_get_verification_email_contents(self):
        subscription = factories.Subscription(
            dataset_id=self.dataset['id'], return_object=True)
        subscription.verification_code = 'testcode'

        subscribe = OgdchSubscribePlugin()
        email_vars = get_verification_email_vars(subscription)
        subject, body_plain_text, body_html = \
            subscribe.get_verification_email_contents(email_vars)

        assert_equal(subject, u'Bestätigungsmail – Abonnement Datensatz - opendata.swiss')
        assert_in(u'''Guten Tag

Sie haben via opendata.swiss die automatische Benachrichtigung über die
Aktualisierungen des folgenden Datensatzes abonniert:''', body_plain_text.strip())
        assert_in(u'''<p>Guten Tag</p>

<p>
    Sie haben via opendata.swiss die automatische Benachrichtigung über die
    Aktualisierungen des folgenden Datensatzes abonniert:
</p>''', body_html.strip())
        assert_not_in(u'http://test.ckan.net', body_html)
        assert_not_in(u'http://test.ckan.net', body_plain_text)

        self._test_html_footer(body_html, subscription=False, code='')
        self._test_plain_text_footer(body_plain_text, subscription=False, code='')
        self._test_all_four_languages(body_html, object_title_included=True)
        self._test_all_four_languages(body_plain_text, object_title_included=True)

    def test_get_manage_email_contents(self):
        subscription = factories.Subscription(
            dataset_id=self.dataset['id'], return_object=True)
        subscription.verification_code = 'testcode'

        subscribe = OgdchSubscribePlugin()
        email_vars = subscribe.get_email_vars(
            code=subscription.verification_code,
            subscription=subscription
        )
        subject, body_plain_text, body_html = \
            subscribe.get_manage_email_contents(email_vars)

        assert_equal(subject, u'Manage opendata.swiss subscription')
        assert_in(u'''Guten Tag

opendata.swiss subscription options:''', body_plain_text.strip())
        assert_in(u'''<p>Guten Tag</p>

<p>opendata.swiss subscription options<br/>''', body_html.strip())
        assert_not_in(u'http://test.ckan.net', body_html)
        assert_not_in(u'http://test.ckan.net', body_plain_text)

        self._test_html_footer(
            body_html, subscription=False, code=subscription.verification_code)
        self._test_plain_text_footer(
            body_plain_text, subscription=False,
            code=subscription.verification_code)
        self._test_all_four_languages(body_html, object_title_included=False)
        self._test_all_four_languages(body_plain_text, object_title_included=False)

    def test_get_subscription_confirmation_email_contents(self):
        subscription = factories.Subscription(
            dataset_id=self.dataset['id'], return_object=True)
        code = 'testcode'

        subscribe = OgdchSubscribePlugin()
        email_vars = subscribe.get_email_vars(
            code=code,
            subscription=subscription
        )
        subject, body_plain_text, body_html = \
            subscribe.get_subscription_confirmation_email_contents(email_vars)

        assert_equal(
            subject,
            u'Bestätigung – Abonnement Account verwalten – opendata.swiss'
        )
        assert_in(u'''Guten Tag

Vielen Dank für Ihre Bestätigung des Datensatz-Abonnements auf opendata.swiss.''',
                  body_plain_text.strip())
        assert_in(u'''<p>Guten Tag</p>

<p>Vielen Dank für Ihre Bestätigung des Datensatz-Abonnements auf opendata.swiss.</p>''',
                  body_html.strip())
        assert_not_in(u'http://test.ckan.net', body_html)
        assert_not_in(u'http://test.ckan.net', body_plain_text)

        self._test_html_footer(
            body_html, subscription=True, code=code)
        self._test_plain_text_footer(
            body_plain_text, subscription=True, code=code)
        self._test_all_four_languages(body_html, object_title_included=False)
        self._test_all_four_languages(body_plain_text, object_title_included=False)

    def test_get_notification_email_contents(self):
        code = 'testcode'
        email = 'bob@example.com'
        subscription = factories.Subscription(
            dataset_id=self.dataset['id'], return_object=False)
        notifications = [
            {
                'subscription': subscription,
                'activities': [
                    {
                        'user_id': 'admin',
                        'object_id': 'test-object-id',
                        'revision_id': 'test-revision-id-1',
                        'activity_type': 'changed package',
                        'timestamp': '2022-10-12T12:00:00',
                        'data': {
                            'package': {
                                'name': 'test-dataset',
                                'title': '{"fr": "FR Test", "de": "DE Test", "en": "EN Test", "it": "IT Test"}',
                            }
                        }
                    }
                ],
            }
        ]

        email_vars = get_notification_email_vars(
            code=code,
            email=email,
            notifications=notifications
        )
        subscribe = OgdchSubscribePlugin()
        subject, body_plain_text, body_html = \
            subscribe.get_notification_email_contents(email_vars)

        assert_equal(
            subject,
            u'Update notification – Aktualisierter Datensatz auf opendata.swiss'
        )
        assert_in(u'''Folgender Datensatz wurde aktualisiert:

- "DE Test": http://frontend-test.ckan.net/dataset/{dataset_id}
'''.format(dataset_id=self.dataset['id']),
                  body_plain_text.strip())
        assert_in(u'''<p>Folgender Datensatz wurde aktualisiert:</p>

<ul>

    <li>
        <a href="http://frontend-test.ckan.net/dataset/{dataset_id}">
            "DE Test" (test-dataset)
        </a>
    </li>

</ul>
'''.format(dataset_id=self.dataset['id']),
                  body_html.strip())
        assert_not_in(u'http://test.ckan.net', body_html)
        assert_not_in(u'http://test.ckan.net', body_plain_text)

        self._test_html_footer(
            body_html, subscription=False, code=code)
        self._test_plain_text_footer(
            body_plain_text, subscription=False, code=code)
        self._test_all_four_languages(body_html, object_title_included=True)
        self._test_all_four_languages(body_plain_text, object_title_included=True)

    def _test_html_footer(self, body_html, subscription=False, code=''):
        assert_in(u'''<p>
    <a href="https://opendata.swiss">
        <img src="https://opendata.swiss/images/logo_horizontal.png" alt="opendata.swiss"
             width="420" style="max-width: 100%; height: auto;"/>
    </a>
</p>
<p>
    <a href="https://twitter.com/opendataswiss">
        <img src="https://opendata.swiss/images/twitter.svg" alt="Twitter"
             style="color: #fff; background-color: #009688; border: 0;"/>
    </a>
</p>''', body_html)

        if code == '':
            footer_link_text = u'<a href="http://frontend-test.ckan.net/subscribe/manage">Mein Abonnement verwalten</a>'
        else:
            footer_link_text = u'<a href="http://frontend-test.ckan.net/subscribe/manage?code={}">Mein Abonnement verwalten</a>'\
                .format(code)
        if subscription:
            footer_link_text = u'<a href="http://frontend-test.ckan.net/subscribe/unsubscribe?code=testcode&amp;dataset={dataset_id}">Abonnement löschen</a> | '\
                                   .format(dataset_id=self.dataset['id']) + footer_link_text

        assert_in(footer_link_text, body_html)

    def _test_plain_text_footer(self, body_plain_text, subscription=False, code=''):
        assert_in(u'''Geschäftsstelle Open Government Data
Bundesamt für Statistik BFS
Espace de l'Europe 10
CH-2010 Neuchâtel
www.bfs.admin.ch/ogd
''', body_plain_text)

        if code == '':
            footer_link_text = u'Mein Abonnement verwalten: http://frontend-test.ckan.net/subscribe/manage'
        else:
            footer_link_text = u'Mein Abonnement verwalten: http://frontend-test.ckan.net/subscribe/manage?code={}'\
                .format(code)
        if subscription:
            footer_link_text = u'Abonnement löschen: http://frontend-test.ckan.net/subscribe/unsubscribe?code=testcode&amp;dataset={dataset_id}\n'\
                                   .format(dataset_id=self.dataset['id']) + footer_link_text

        assert_in(footer_link_text, body_plain_text)

    def _test_all_four_languages(self, body, object_title_included=False):
        if object_title_included:
            assert_in('DE Test', body)
            assert_in('EN Test', body)
            assert_in('FR Test', body)
            assert_in('IT Test', body)

        # Check that there is a sign-off in each language
        assert_in(u'Team Geschäftsstelle OGD', body)
        assert_in(u'Team Open Government Data Office', body)
        assert_in(u'Votre Team Secrétariat OGD', body)
        assert_in(u'Team Segreteria OGD', body)
