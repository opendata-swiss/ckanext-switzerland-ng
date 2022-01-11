"""Tests for logic."""

import ckanext.switzerland.logic as logic
import nose

from ckan.lib.helpers import url_for
import ckan.plugins.toolkit as tk
import ckan.model as model

from ckan.tests import helpers, factories
import logging
log = logging.getLogger(__name__)

assert_equal = nose.tools.assert_equal
assert_true = nose.tools.assert_true


class TestLogic(helpers.FunctionalTestBase):

    @classmethod
    def teardown_class(cls):
        super(TestLogic, cls).teardown_class()
        helpers.reset_db()

    def setup(self):
        super(TestLogic, self).setup()
        user = tk.get_action('get_site_user')({'ignore_auth': True})['name']
        self.context = {'model': model, 'session': model.Session,
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
        tk.get_action('organization_create')(self.context, self.org)

        # create a valid DCAT-AP Switzerland compliant dataset
        self.dataset = {
            'coverage': '',
            'id': 'b0377d3c-5583-4c7d-81bc-ec7aa8f60ae2',
            'issued': '08.09.2015',
            'contact_points': [{'email': 'pierre@bar.ch', 'name': 'Pierre'}],
            'keywords': {
                'fr': [],
                'de': [],
                'en': [],
                'it': []
            },
            'spatial': '',
            'publishers': [{'label': 'Bundesarchiv'}],
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
            'accrual_periodicity': 'http://purl.org/cld/freq/completelyIrregular',
            'modified': '09.09.2015',
            'url': 'http://some_url',
            'owner_org': 'test-org',
            'identifier': 'test@test-org'
        }


    def test_correct_temporals_format(self):

        # self.dataset["temporals"] = [
        #         {
        #             "start_date": "2020-03-05T00:00:00",
        #             "end_date": "2021-12-22T00:00:00"
        #         }
        #     ]
        tk.get_action('package_create')(self.context, self.dataset)

        result = logic.ogdch_package_patch(self.context, self.dataset)

        log.info("========================")
        log.info("result")
        log.info(result)
        log.info("========================")

        #start_date_str = self._temporals(dataset)
        #end_date_str = self._temporals(dataset)


