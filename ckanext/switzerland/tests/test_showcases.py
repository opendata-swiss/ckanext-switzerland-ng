from unittest.mock import call, patch

import ckan.plugins.toolkit as tk
import pytest

from ckanext.switzerland.tests.conftest import get_context, public_showcase_data


@pytest.mark.ckan_config("ckan.plugins", "ogdch_showcase")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestShowcaseApi(object):
    @patch("ckanext.switzerland.logic.send_showcase_email")
    def test_create_showcase(self, mock_send_showcase_email_obj, groups):
        showcase = tk.get_action("ckanext_showcase_create")(
            get_context(), public_showcase_data
        )
        assert showcase["name"] == "animal-diseases"
        assert showcase["showcase_type"] == "data_visualization"
        assert showcase["private"] is False
        assert showcase["author"] == "Maria Muster"
        assert showcase["author_email"] == "maria.muster@example.org"
        assert showcase["author_twitter"] == "https://twitter.com@mariamuster"
        assert showcase["author_github"] == "https://github.com/mariamuster"
        assert showcase["groups"][0]["name"] == "group1"
        assert showcase["tags"][0]["name"] == "animals"

        mock_send_showcase_email_obj.assert_has_calls([call(showcase)])

    def test_list_showcases(self, showcases):
        """The showcases fixture creates two showcases, one public and one private.
        Test that the API only returns one showcase, and it is the public one.
        """
        assert len(showcases) == 2
        assert showcases[0]["private"] is False
        assert showcases[1]["private"] is True

        showcases_from_api = tk.get_action("ckanext_showcase_list")(get_context(), {})
        assert len(showcases_from_api) == 1
        assert showcases[0]["name"] == "animal-diseases"
        assert showcases[0]["private"] is False
