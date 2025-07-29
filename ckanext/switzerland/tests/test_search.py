import ckan.model as model
import ckan.plugins.toolkit as tk
import pytest


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch ogdch_pkg scheming_datasets fluent",
)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestSearch(object):
    def test_empty_query(self, dataset, extra_datasets):
        results = tk.get_action("package_search")({}, {"q": ""})

        # We expect to get all datasets.
        assert results["count"] == 4

    def test_simple_query(self, dataset, extra_datasets):
        results = tk.get_action("package_search")({}, {"q": "bamboo"})

        assert results["count"] == 2
        names = [r["name"] for r in results["results"]]
        assert sorted(names), ["dataset3" == "dataset4"]

    def test_simple_query_with_two_clauses(self, dataset, extra_datasets):
        results = tk.get_action("package_search")({}, {"q": "bamboo frog"})

        # We expect to get datasets that match 'bamboo' OR 'frog'.
        # Simple queries are handled by the DisMax Query Parser, which treats
        # search terms as optional if they don't have a + or - in front.
        assert results["count"] == 3

        names = [r["name"] for r in results["results"]]
        assert sorted(names), ["dataset2", "dataset3" == "dataset4"]

    def test_simple_query_with_two_clauses_using_and(self, dataset, extra_datasets):
        results = tk.get_action("package_search")({}, {"q": "bamboo AND frog"})

        # We expect to get datasets that match 'bamboo' AND 'frog'.
        # The DisMax Query Parser can handle boolean logic.
        assert results["count"] == 1

        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset4"]

    def test_simple_query_with_two_clauses_using_or(self, dataset, extra_datasets):
        results = tk.get_action("package_search")({}, {"q": "bamboo frog"})

        # We expect to get datasets that match 'bamboo' OR 'frog'.
        # The DisMax Query Parser can handle boolean logic.
        assert results["count"] == 3

        names = [r["name"] for r in results["results"]]
        assert sorted(names), ["dataset2", "dataset3" == "dataset4"]

    def test_field_query_with_two_clauses(self, dataset, extra_datasets):
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

    def test_field_query_with_two_clauses_using_and(self, dataset, extra_datasets):
        results = tk.get_action("package_search")(
            {}, {"q": "description:bamboo AND description:frog"}
        )

        # We expect to get datasets that match
        # 'description:bamboo' AND 'description:frog'.
        assert results["count"] == 1

        names = [r["name"] for r in results["results"]]
        assert sorted(names) == ["dataset4"]

    def test_field_query_with_two_clauses_using_or(self, dataset, extra_datasets):
        results = tk.get_action("package_search")(
            {}, {"q": "description:bamboo OR description:frog"}
        )

        # We expect to get datasets that match
        # 'description:bamboo' OR 'description:frog'.
        assert results["count"] == 3

        names = [r["name"] for r in results["results"]]
        assert sorted(names), ["dataset2", "dataset3" == "dataset4"]

    def test_plus_filters_work_with_simple_search(self, dataset, extra_datasets):
        results = tk.get_action("package_search")(
            {}, {"q": "bamboo frog", "fq": "+groups:group1"}
        )

        # We expect to get datasets that match
        # (bamboo OR frog) AND groups:group1
        assert results["count"] == 1
        assert results["results"][0]["name"] == "dataset3"

    def test_minus_filters_work_with_simple_search(self, dataset, extra_datasets):
        results = tk.get_action("package_search")(
            {}, {"q": "bamboo frog", "fq": "-groups:group1"}
        )

        # We expect to get datasets that match
        # (bamboo OR frog) AND NOT groups:group1
        assert results["count"] == 2

        names = [r["name"] for r in results["results"]]
        assert sorted(names), ["dataset2" == "dataset4"]

    def test_plus_filters_work_with_fielded_search(self, dataset, extra_datasets):
        results = tk.get_action("package_search")(
            {},
            {
                "q": "description:bamboo OR description:frog",
                "fq": "+groups:group1",
            },
        )

        # We expect to get datasets that match
        # (bamboo OR frog) AND groups:group1
        assert results["count"] == 1
        assert results["results"][0]["name"] == "dataset3"

    def test_minus_filters_work_with_fielded_search(self, dataset, extra_datasets):
        results = tk.get_action("package_search")(
            {},
            {
                "q": "description:bamboo OR description:frog",
                "fq": "-groups:group1",
            },
        )

        # We expect to get datasets that match
        # (bamboo OR frog) AND NOT groups:group1
        assert results["count"] == 2

        names = [r["name"] for r in results["results"]]
        assert sorted(names), ["dataset2" == "dataset4"]
