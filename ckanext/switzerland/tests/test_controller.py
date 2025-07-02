import nose
from ckan.lib.helpers import url_for

from ckanext.switzerland.tests import OgdchFunctionalTestBase

assert_equal = nose.tools.assert_equal
assert_true = nose.tools.assert_true


class TestController(OgdchFunctionalTestBase):
    def test_valid_redirect(self):
        app = self._get_test_app()

        url = url_for("perma_redirect", id=self.dataset_dict["identifier"])
        assert_equal(url, "/perma/test%40test-org")

        response = app.get(url)
        assert_equal(response.status_int, 302)
        assert_equal(
            response.headers.get("Location"),
            "http://test.ckan.net/dataset/test-dataset",
        )

    def test_invalid_redirect(self):
        app = self._get_test_app()

        url = url_for("perma_redirect", id="non-existent-id@unknown")
        assert_equal(url, "/perma/non-existent-id%40unknown")

        # expect a 404 response
        response = app.get(url, status=404)

    def test_org_list_links(self):
        app = self._get_test_app()

        # no locale, should default to EN
        url = url_for("organizations_index")
        assert url.startswith("/organization"), (
            f"URL {url} does not start with /organization"
        )

        response = app.get(url, status=200)

        assert "/en/organization/test-org" in response

        # set locale via CKAN_LANG to IT
        response = app.get(
            url, status=200, extra_environ={"CKAN_LANG": "it", "CKAN_CURRENT_URL": url}
        )

        assert "/it/organization/test-org" in response

        # locale DE
        url = url_for("organizations_index", locale="de")
        assert url.startswith("/de/organization"), (
            f"URL {url} does not start with /de/organization"
        )

        response = app.get(url, status=200)

        assert "/de/organization/test-org" in response

        # locale FR
        url = url_for("organizations_index", locale="fr")
        assert url.startswith("/fr/organization"), (
            f"URL {url} does not start with /fr/organization"
        )

        response = app.get(url, status=200)

        assert "/fr/organization/test-org" in response
