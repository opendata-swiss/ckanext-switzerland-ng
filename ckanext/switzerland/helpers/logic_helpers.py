"""
helpers for the plugin logic
"""

import ckan.plugins.toolkit as tk
from ckan import model as model


def get_org_count():
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    req_context = {"user": user["name"]}
    orgs = tk.get_action("organization_list")(req_context, {})
    return len(orgs)


def get_dataset_count(dataset_type="dataset"):
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    req_context = {"user": user["name"]}
    fq = "".join(["+dataset_type:", dataset_type])
    packages = tk.get_action("package_search")(req_context, {"fq": fq})
    return packages["count"]


def get_showcases_for_dataset(id):
    """
    Return a list of showcases a dataset is associated with
    """
    context = {
        "model": model,
        "session": model.Session,
        "user": tk.c.user or tk.c.author,
        "for_view": True,
        "auth_user_obj": tk.c.userobj,
    }
    data_dict = {"package_id": id}

    try:
        return tk.get_action("ckanext_package_showcase_list")(context, data_dict)
    except tk.NotFound:
        return None


def map_existing_resources_to_new_dataset(new_dataset, existing_dataset):
    existing_resources = existing_dataset.get("resources")
    resource_mapping = {
        r.get("uri"): r.get("id") for r in existing_resources if r.get("uri")
    }
    for resource in new_dataset.get("resources"):
        res_uri = resource.get("uri")
        if res_uri and res_uri in resource_mapping:
            resource["id"] = resource_mapping[res_uri]
