import nose

assert_equal = nose.tools.assert_equal
assert_true = nose.tools.assert_true


class TestMiddleware(object):
    def test_response_header_html(self, app):
        response = app.get("/dataset/test-dataset")

        assert_equal(response.status_int, 200)
        assert_equal(response.headers.get("X-Robots-Tag"), "noindex, nofollow")

    def test_response_header_xml(self, app):
        response = app.get("/dataset/test-dataset.xml")

        assert_equal(response.status_int, 200)
        assert_equal(response.headers.get("X-Robots-Tag"), "noindex, nofollow")

    def test_response_header_json(self, app):
        response = app.get("/api/3/action/package_show?id=test-dataset")

        assert_equal(response.status_int, 200)
        assert_equal(response.headers.get("X-Robots-Tag"), "noindex, nofollow")
