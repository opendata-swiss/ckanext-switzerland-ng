"""Tests for logic."""
import os
from datetime import datetime
import ckanext.switzerland.logic as logic

class TestBaseObj(object):

    def _temporals(self, dataset):
        start_date = []
        end_date = []

        for temporal in dataset.get('temporals'):
            start_date.append( map(lambda d: d['start_date'], temporal)[0])
            end_date.append(map(lambda d: d['end_date'], temporal)[0])
        return start_date, end_date

    dataset = {
                'id': '4b6fe9ca-dc77-4cec-92a4-55c6624a5bd6',
                'name': 'test-dataset',
                'title': 'Test DCAT dataset',
                'url': 'http://example.com/ds1',
                'version': '1.0b',
                'metadata_created': '2015-06-26T15:21:09.034694',
                'metadata_modified': '2015-06-26T15:21:09.075774',
                "keywords": {
                    "fr": [],
                    "de": [
                        "covid19",
                        "fallzahlen",
                        "thurgau"
                    ],
                    "en": [],
                    "it": []
                }
            }

class TestLogic(TestBaseObj):
    def test_correct_temporals_format(self):
        dataset["temporals"] = [
                {
                    "start_date": "2020-03-05T00:00:00",
                    "end_date": "2021-12-22T00:00:00"
                }
            ]


        result = logic.ogdch_package_patch(dataset)
        print(result)
        #start_date_str = self._temporals(dataset)
        #end_date_str = self._temporals(dataset)


