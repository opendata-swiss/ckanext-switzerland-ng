from unittest.mock import call, patch

import ckan.plugins.toolkit as tk
import pytest

from ckanext.switzerland.tests.conftest import get_context

showcase_data = {
    "name": "animal-diseases",
    "title": "Animal Diseases",
    "url": "https://jupyter.zazuko.com/epidemics.html",
    "author": "Maria Muster",
    "author_email": "maria.muster@example.org",
    "notes": "FSVO, Federal Food Safety and Veterinary Office,\r\ncollects data on the animal diseases in Switzerland.\r\nThis data is published as [Linked Data](https://en.wikipedia.org/wiki/Linked_data).\r\n\r\nIn this data story, we will show how to work with Linked\r\nData. Mainly, we will see how to work with data on\r\nanimal disease.\r\n\r\n__Used Datasets__:\r\n\r\n\r\n- API: https://s.zazuko.com/2RxKQF\r\n\r\n\r\n\r\n- Metadata: https://environment.ld.admin.ch/foen/animal-pest/dataset",
    "owner_org": "test-org",
    "private": False,
    "state": "active",
    "tags": [{"name": "animals"}],
    "image_url": "https://zazuko.com/data-stories/cat.jpg",
    "showcase_type": "data_visualization",
    "groups": [{"name": "group1"}],
    "author_twitter": "https://twitter.com@mariamuster",
    "author_github": "https://github.com/mariamuster",
}


def mock_send_showcase_email(showcase_dict):
    pass


@pytest.mark.ckan_config("ckan.plugins", "ogdch_showcase")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestShowcaseApi(object):
    @patch("ckanext.switzerland.logic.send_showcase_email")
    def test_create_showcase(
        self, mock_send_showcase_email_obj, app, site_user, org, groups
    ):
        showcase = tk.get_action("ckanext_showcase_create")(
            get_context(), showcase_data
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
