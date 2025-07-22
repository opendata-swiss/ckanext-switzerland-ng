import pytest
from ckan.lib.helpers import url_for


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch ogdch_pkg ogdch_showcase scheming_datasets fluent hierarchy_display",
)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestBlueprints(object):
    def test_valid_redirect(self, app, dataset):
        url = url_for("perma.read", id=dataset["identifier"])
        assert url == "/perma/test@test-org"

        response = app.get(url)
        assert response.status_int == 302
        assert (
            response.headers.get("Location")
            == "http://test.ckan.net/dataset/test-dataset"
        )

    def test_invalid_redirect(self, app):
        url = url_for("perma.read", id="non-existent-id@unknown")
        assert url == "/perma/non-existent-id@unknown"

        # expect a 404 response
        response = app.get(url, status=404)

    def test_org_list_links(self, app, org):
        # no locale, should default to EN
        url = url_for("organization.index")
        assert url.startswith(
            "/organization"
        ), f"URL {url} does not start with /organization"

        response = app.get(url, status=200)

        assert "/en/organization/test-org" in response

        # set locale via CKAN_LANG to IT
        response = app.get(
            url, status=200, extra_environ={"CKAN_LANG": "it", "CKAN_CURRENT_URL": url}
        )

        assert "/it/organization/test-org" in response

        # locale DE
        url = url_for("organization.index", locale="de")
        assert url.startswith(
            "/de/organization"
        ), f"URL {url} does not start with /de/organization"

        response = app.get(url, status=200)

        assert "/de/organization/test-org" in response

        # locale FR
        url = url_for("organization.index", locale="fr")
        assert url.startswith(
            "/fr/organization"
        ), f"URL {url} does not start with /fr/organization"

        response = app.get(url, status=200)

        assert "/fr/organization/test-org" in response
