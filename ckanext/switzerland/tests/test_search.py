from copy import copy

import ckan.model as model
import ckan.plugins.toolkit as tk
import nose

from ckanext.switzerland.tests import OgdchFunctionalTestBase

assert_equal = nose.tools.assert_equal
assert_true = nose.tools.assert_true


class TestSearch(OgdchFunctionalTestBase):
    def _get_context(self):
        # We need a fresh context every time we create a dataset
        user = tk.get_action("get_site_user")({"ignore_auth": True})["name"]
        return {
            "model": model,
            "session": model.Session,
            "user": user,
            "ignore_auth": True,
        }

    def setup(self):
        # This creates an org and a dataset in the database.
        super(TestSearch, self).setup()

        # Add some more datasets
        dataset_dict_2 = copy(self.dataset_dict)
        dataset_dict_2["name"] = "dataset2"
        dataset_dict_2["identifier"] = "dataset2@test-org"
        dataset_dict_2["description"] = {
            "fr": "Frog FR",
            "de": "Frog DE",
            "en": "Frog EN",
            "it": "Frog IT",
        }
        tk.get_action("package_create")(self._get_context(), dataset_dict_2)

        dataset_dict_3 = copy(self.dataset_dict)
        dataset_dict_3["name"] = "dataset3"
        dataset_dict_3["identifier"] = "dataset3@test-org"
        dataset_dict_3["description"] = {
            "fr": "Bamboo FR",
            "de": "Bamboo DE",
            "en": "Bamboo EN",
            "it": "Bamboo IT",
        }
        dataset_dict_3["keywords"] = {
            u"fr": [u"tag-fr"],
            u"de": [],
            u"en": [],
            u"it": [],
        }

        tk.get_action("package_create")(self._get_context(), dataset_dict_3)

        dataset_dict_4 = copy(self.dataset_dict)
        dataset_dict_4["name"] = "dataset4"
        dataset_dict_4["identifier"] = "dataset4@test-org"
        dataset_dict_4["description"] = {
            "fr": "Bamboo Frog FR",
            "de": "Bamboo Frog DE",
            "en": "Bamboo Frog EN",
            "it": "Bamboo Frog IT",
        }
        dataset_dict_3["keywords"] = {
            u"fr": [],
            u"de": [u"tag-de"],
            u"en": [],
            u"it": [],
        }

        tk.get_action("package_create")(self._get_context(), dataset_dict_4)

    def test_empty_query(self):
        results = tk.get_action("package_search")({}, {"q": ""})

        # We expect to get all datasets.
        assert results["count"] == 4

    def test_simple_query(self):
        results = tk.get_action("package_search")({}, {"q": "bamboo"})

        assert results["count"] == 2
        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset3", "dataset4"]

    def test_simple_query_with_two_clauses(self):
        results = tk.get_action("package_search")({}, {"q": "bamboo frog"})

        # We expect to get datasets that match 'bamboo' OR 'frog'.
        # Simple queries are handled by the DisMax Query Parser, which treats
        # search terms as optional if they don't have a + or - in front.
        assert results["count"] == 3

        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset2", "dataset3", "dataset4"]

    def test_simple_query_with_two_clauses_using_and(self):
        results = tk.get_action("package_search")({}, {"q": "bamboo AND frog"})

        # We expect to get datasets that match 'bamboo' AND 'frog'.
        # The DisMax Query Parser can handle boolean logic.
        assert results["count"] == 1

        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset4"]

    def test_simple_query_with_two_clauses_using_or(self):
        results = tk.get_action("package_search")({}, {"q": "bamboo frog"})

        # We expect to get datasets that match 'bamboo' OR 'frog'.
        # The DisMax Query Parser can handle boolean logic.
        assert results["count"] == 3

        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset2", "dataset3", "dataset4"]

    def test_field_query_with_two_clauses(self):
        results = tk.get_action("package_search")(
            {}, {"q": "description:bamboo description:frog"}
        )

        # We expect to get datasets that match
        # 'description:bamboo' AND 'description:frog'.
        # Fielded queries are handled by the eDisMax Query Parser, which has a
        # default search operator of AND.
        assert results["count"] == 1

        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset4"]

    def test_field_query_with_two_clauses_using_and(self):
        results = tk.get_action("package_search")(
            {}, {"q": "description:bamboo AND description:frog"}
        )

        # We expect to get datasets that match
        # 'description:bamboo' AND 'description:frog'.
        assert results["count"] == 1

        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset4"]

    def test_field_query_with_two_clauses_using_or(self):
        results = tk.get_action("package_search")(
            {}, {"q": "description:bamboo OR description:frog"}
        )

        # We expect to get datasets that match
        # 'description:bamboo' OR 'description:frog'.
        assert results["count"] == 3

        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset2", "dataset3", "dataset4"]

    def test_plus_filters_work_with_simple_search(self):
        results = tk.get_action("package_search")(
            {}, {"q": "bamboo frog", "fq": "+keywords_fr:tag-fr"}
        )

        # We expect to get datasets that match
        # (bamboo OR frog) AND keywords_fr:tag-fr
        assert results["count"] == 1
        assert results["results"][0]["name"] == "dataset3"

    def test_minus_filters_work_with_simple_search(self):
        results = tk.get_action("package_search")(
            {}, {"q": "bamboo frog", "fq": "-keywords_fr:tag-fr"}
        )

        # We expect to get datasets that match
        # (bamboo OR frog) AND NOT keywords_fr:tag-fr
        assert results["count"] == 2

        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset2", "dataset4"]

    def test_plus_filters_work_with_fielded_search(self):
        results = tk.get_action("package_search")(
            {},
            {
                "q": "description:bamboo OR description:frog",
                "fq": "+keywords_fr:tag-fr",
            },
        )

        # We expect to get datasets that match
        # (bamboo OR frog) AND keywords_fr:tag-fr
        assert results["count"] == 1
        assert results["results"][0]["name"] == "dataset3"

    def test_minus_filters_work_with_fielded_search(self):
        results = tk.get_action("package_search")(
            {},
            {
                "q": "description:bamboo OR description:frog",
                "fq": "-keywords_fr:tag-fr",
            },
        )

        # We expect to get datasets that match
        # (bamboo OR frog) AND NOT keywords_fr:tag-fr
        assert results["count"] == 2

        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset2", "dataset4"]
