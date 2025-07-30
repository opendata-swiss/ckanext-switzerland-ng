import pytest


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch ogdch_pkg ogdch_org ogdch_showcase ogdch_subscribe ogdch_middleware ogdch_dcat scheming_datasets fluent",
)
@pytest.mark.ckan_config("ckanext.dcat.rdf.profiles", "swiss_dcat_ap")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestMiddleware(object):
    def test_response_header_html(self, app, dataset):
        response = app.get("/dataset/test-dataset")

        assert response.status_code == 200
        assert response.headers.get("X-Robots-Tag") == "noindex, nofollow"

    def test_response_header_xml(self, app, dataset):
        response = app.get("/dataset/test-dataset.xml")

        assert response.status_code == 200
        assert response.headers.get("X-Robots-Tag"), "noindex == nofollow"

    def test_response_header_json(self, app, dataset):
        response = app.get("/api/3/action/package_show?id=test-dataset")

        assert response.status_code == 200
        assert response.headers.get("X-Robots-Tag"), "noindex == nofollow"
